from rai_digital_twin.models.digital_twin_v1.model.params import NUMERICAL_PARAMS
from time import time
from typing import Any
from pandas.core.frame import DataFrame
import pandas as pd
from datetime import datetime, timedelta
from os import listdir
from pathlib import Path
from cadCAD_tools import easy_run
from cadCAD_tools.preparation import prepare_params, Param, ParamSweep
from json import dump
import papermill as pm
import os

# Module dependencies
from .retrieve_data import download_data
from .prepare_data import load_backtesting_data, load_governance_events
from .backtesting import simulation_loss
from .stochastic import FitParams, fit_eth_price, generate_eth_samples
from rai_digital_twin import default_model
from rai_digital_twin.types import ActionState, BacktestingData, ControllerParams, ControllerState, Days, ExogenousData, Percentage
from rai_digital_twin.types import GovernanceEvent, Timestep, USD_per_ETH


def retrieve_data(output_path: str,
                  date_range: tuple[Any, Any]) -> DataFrame:
    """
    Download all requried data
    """
    df = download_data(date_range=date_range)
    df.to_csv(output_path, compression='gzip')
    return df


def prepare(input_path: str,
            governance_input_path) -> tuple[BacktestingData,
                                            dict[Timestep, GovernanceEvent]]:
    """
    Clean-up required historical and prior data.
    """
    backtesting_data = load_backtesting_data(input_path)

    governance_events = load_governance_events(governance_input_path,
                                               backtesting_data.heights)

    # TODO run notebook template

    return (backtesting_data, governance_events)


def backtest_model(backtesting_data: BacktestingData,
                   governance_events) -> tuple[DataFrame, DataFrame, DataFrame]:
    """
    Perform historical backtesting by using the past controller state
    and token states.
    """

    initial_state = default_model.initial_state

    initial_pid_state = ControllerState(backtesting_data.pid_states[0].redemption_price,
                                        backtesting_data.pid_states[0].redemption_rate,
                                        0.0,
                                        0.0)

    initial_state.update(pid_state=initial_pid_state,
                         token_state=backtesting_data.token_states[0])
    if 0 in governance_events:
        first_event = governance_events[0].descriptor
        initial_pid_params = ControllerParams(first_event['kp'],
                                              first_event['ki'],
                                              first_event['leaky_factor'],
                                              first_event['period'],
                                              first_event['enabled'])
        initial_state.update(pid_params=initial_pid_params)

    params = default_model.parameters
    params.update(heights=Param(backtesting_data.heights, None))
    params.update(governance_events=Param(governance_events, None))
    params.update(backtesting_data=Param(backtesting_data.token_states, None))
    params.update(exogenous_data=Param(backtesting_data.exogenous_data, None))

    timesteps = len(backtesting_data.heights) - 1

    params = prepare_params(params)
    raw_sim_df = easy_run(initial_state,
                          params,
                          default_model.timestep_block,
                          timesteps,
                          1,
                          drop_substeps=True,
                          assign_params=False)

    sim_df = default_model.post_processing(raw_sim_df)
    test_df = pd.DataFrame.from_dict(
        backtesting_data.pid_states, orient='index')
    loss = simulation_loss(sim_df, test_df)
    print(f"Backtesting loss: {loss :.2%}")

    return (sim_df, test_df, raw_sim_df)


def stochastic_fit(input_data: object) -> FitParams:
    """
    Acquire parameters for the stochastic input signals.
    """

    X = pd.DataFrame(input_data).T.eth_price
    params = fit_eth_price(X)
    return params


def extrapolate_signals(signal_params: FitParams,
                        timesteps: int,
                        initial_price: USD_per_ETH,
                        N_samples=3) -> tuple[ExogenousData, ...]:
    """
    Generate input signals from given parameters.
    """
    eth_series_list = generate_eth_samples(signal_params,
                                           timesteps,
                                           N_samples,
                                           initial_price)

    # Clean-up data for injecting on the cadCAD model
    exogenous_data_sweep = tuple(tuple({'eth_price': el}
                                       for el
                                       in eth_series)
                                 for eth_series
                                 in eth_series_list)

    return exogenous_data_sweep


def extrapolate_data(signals: object,
                     backtest_results: tuple[DataFrame, DataFrame, DataFrame],
                     governance_events,
                     N_t: int = 10,
                     N_samples: int = 3) -> DataFrame:
    """
    Generate a extrapolation dataset.
    """
    (sim_df, test_df, raw_sim_df) = backtest_results

    # Index for the last available data points
    last_row = raw_sim_df.iloc[-1]
    last_historical_row = test_df.iloc[-1]

    initial_state = default_model.initial_state
    initial_pid_state = ControllerState(last_historical_row.redemption_price,
                                        last_historical_row.redemption_rate,
                                        0.0,
                                        0.0)

    initial_pid_params = last_row['pid_params']

    # Append all past action states for usage on the fit-predict process
    cols = {'token_state',
            'pid_state',
            'market_price',
            'eth_price'}
    # TODO use pid_state from test_df rather than sim_df
    records = (raw_sim_df.reset_index()
               .loc[:, cols]
               .to_dict(orient='records'))
    past_action_states = [ActionState(**record) for record in records]

    # Update system parameters for extrapolation
    params = default_model.parameters
    params.update(perform_backtesting=Param(False, bool))
    params.update(heights=Param(None, bool))
    params.update(backtesting_data=Param(None, bool))
    # TODO: use governance events on the extrapolation itself
    params.update(governance_events=Param({}, dict))
    params.update(exogenous_data=ParamSweep(signals, None))
    params.update(backtesting_action_states=Param(past_action_states, None))
    params.update(use_ewm_model=ParamSweep([False, True], Percentage))
    params.update(convergence_swap_intensity=ParamSweep([None, 0.25], Percentage))
    prepared_params = prepare_params(params, cartesian_sweep=True)

    # Update initial state for extrapolation
    initial_state.update(pid_state=initial_pid_state,
                         pid_params=initial_pid_params,
                         token_state=last_row.token_state,
                         eth_price=last_row.eth_price,
                         spot_price=last_row.spot_price,
                         market_price=last_row.market_price)  # TODO use test df state

    # Run extrapolation simulation
    sim_df = easy_run(initial_state,
                      prepared_params,
                      default_model.timestep_block,
                      N_t,
                      N_samples,
                      drop_substeps=True,
                      assign_params=NUMERICAL_PARAMS)

    # Clean-up
    sim_df = default_model.post_processing(sim_df)

    return sim_df


def extrapolation_cycle(base_path: str = None,
                        historical_interval: Days = 14,
                        historical_lag: Days = 0,
                        price_samples: int = 10,
                        extrapolation_samples: int = 1,
                        extrapolation_timesteps: int = 7 * 24,
                        use_last_data=False,
                        generate_reports=True) -> object:
    """
    Perform a entire extrapolation cycle.
    """
    t1 = time()
    print("0. Retrieving Data\n---")
    runtime = datetime.utcnow()

    if base_path is None:
        working_path = Path(os.getcwd())
        data_path = working_path / 'data/runs'
    else:
        working_path = Path(base_path)
        data_path = working_path / 'data/runs'

    governance_data_path = working_path / 'data/controller_params.csv'
    
    if use_last_data is False:
        date_end = runtime - timedelta(days=historical_lag)
        date_start = date_end - timedelta(days=historical_interval)
        date_range = (date_start, date_end)

        historical_data_path = data_path / f'{runtime}_retrieval.csv.gz'
        retrieve_data(str(historical_data_path),
                      date_range)
        print(f"Data written at {historical_data_path}")
    else:
        files = listdir(data_path.expanduser())
        files = sorted(
            file for file in files if 'retrieval.csv.gz' in file)
        historical_data_path = data_path / f'{files[-1]}'
        print(f"Using last data at {historical_data_path}")

    print("1. Preparing Data\n---")
    backtesting_data, governance_events = prepare(str(historical_data_path),
                                                  str(governance_data_path)
                                                  )

    print("2. Backtesting Model\n---")
    backtest_results = backtest_model(backtesting_data, governance_events)

    backtest_results[0].to_csv(data_path / f'{runtime}-backtesting.csv.gz',
                               compression='gzip',
                               index=False)

    backtest_results[1].to_csv(data_path / f'{runtime}-historical.csv.gz',
                               compression='gzip',
                               index=False)

    timestamps = sorted([el['timestamp']
                         for (timestep, el)
                         in backtesting_data.exogenous_data.items()])

    metadata = {'createdAt': str(runtime),
                'initial_backtesting_timestamp': str(timestamps[0]),
                'final_backtesting_timestamp': str(timestamps[-1])}

    with open(data_path.expanduser() / f"{runtime}-meta.json", 'w') as fid:
        dump(metadata, fid)

    print("3. Fitting Stochastic Processes\n---")
    stochastic_params = stochastic_fit(backtesting_data.exogenous_data)

    print("4. Extrapolating Exogenous Signals\n---")
    N_t = extrapolation_timesteps
    N_price_samples = price_samples
    initial_price = backtest_results[0].iloc[-1].eth_price
    extrapolated_signals = extrapolate_signals(stochastic_params,
                                               N_t + 10,
                                               initial_price,
                                               N_price_samples)

    print("5. Extrapolating Future Data\n---")
    N_extrapolation_samples = extrapolation_samples
    extrapolation_df = extrapolate_data(extrapolated_signals,
                                        backtest_results,
                                        governance_events,
                                        N_t,
                                        N_extrapolation_samples)

    extrapolation_df.to_csv(data_path / f'{runtime}-extrapolation.csv.gz',
                            compression='gzip',
                            index=False)

    print("6. Exporting results\n---")
    if generate_reports == True:
        path = str((data_path / f'{runtime}-').expanduser())
        input_nb_path = (
            working_path / 'rai_digital_twin/templates/extrapolation.ipynb').expanduser()
        output_nb_path = (
            working_path / f'reports/{runtime}-extrapolation.ipynb').expanduser()
        output_html_path = (
            working_path / f'reports/{runtime}-extrapolation.html').expanduser()
        pm.execute_notebook(
            input_nb_path,
            output_nb_path,
            parameters=dict(base_path=path)
        )
        export_cmd = f"jupyter nbconvert --to html '{output_nb_path}'"
        os.system(export_cmd)
        os.system(f"rm '{output_nb_path}'")
    t2 = time()
    print(f"7. Done! {t2 - t1 :.2f}s\n---")

    output = (backtest_results, extrapolation_df, stochastic_params)
    return output
