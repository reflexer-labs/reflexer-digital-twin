
from pandas.core.frame import DataFrame
from rai_digital_twin.types import ActionState, BacktestingData, ControllerParams, ControllerState, GovernanceEvent, Timestep, TimestepDict
import pandas as pd

from cadCAD_tools import easy_run
from .backtesting import simulation_loss
from .prepare_data import load_backtesting_data, load_governance_events
from .stochastic import FitParams, fit_eth_price, generate_eth_samples
from rai_digital_twin import default_model
from time import time

BACKTESTING_DATA_PATH = '~/repos/bsci/reflexer-digital-twin/data/states.csv'
GOVERNANCE_EVENTS_PATH = '~/repos/bsci/reflexer-digital-twin/data/controller_params.csv'


def prepare(report_path: str = None) -> tuple[BacktestingData,
                                              dict[Timestep, GovernanceEvent]]:
    """
    Retrieves all required historical and prior data.
    """
    backtesting_data = load_backtesting_data(BACKTESTING_DATA_PATH)

    governance_events = load_governance_events(GOVERNANCE_EVENTS_PATH,
                                               backtesting_data.heights)

    return (backtesting_data, governance_events)


def backtest_model(backtesting_data: BacktestingData,
                   governance_events) -> tuple[DataFrame, DataFrame, DataFrame]:

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
    params.update(heights=[backtesting_data.heights])
    params.update(governance_events=[governance_events])
    params.update(backtesting_data=[backtesting_data.token_states])
    params.update(exogenous_data=[backtesting_data.exogenous_data])

    timesteps = len(backtesting_data.heights) - 1

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

    # TODO run notebook template

    return (sim_df, test_df, raw_sim_df)


def stochastic_fit(input_data: object,
                   report_path: str = None) -> dict:
    """
    Acquire parameters for the stochastic input signals.
    """

    X = pd.DataFrame(input_data).T.eth_price
    params = fit_eth_price(X)

    # TODO run notebook template

    return params


def extrapolate_signals(signal_params: FitParams,
                        timesteps: int,
                        report_path: str = None) -> object:
    """
    Generate input signals from given parameters.
    """
    samples = 1  # TODO
    eth_series = list(generate_eth_samples(signal_params, timesteps, samples))
    eth_price_list: list = eth_series[0]
    exogenous_data = {t: {'eth_price': el}
                      for t, el in enumerate(eth_price_list)}

    # TODO run notebook template

    return exogenous_data


def extrapolate_data(signals: object,
                     backtesting_data: BacktestingData,
                     backtest_results: DataFrame,
                     governance_events,
                     N_t: int = 10,
                     report_path: str = None) -> object:
    """
    Generate a extrapolation dataset.
    """
    (sim_df, test_df, raw_sim_df) = backtest_results

    # Index for the last available data points
    last_row = raw_sim_df.iloc[-1]

    initial_state = default_model.initial_state
    # TODO use test_df pid state
    initial_pid_state = ControllerState(last_row.pid_state.redemption_price,
                                        last_row.pid_state.redemption_rate,
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
    params.update(perform_backtesting=[False])
    params.update(heights=[None])
    params.update(backtesting_data=[None])
    params.update(governance_events=[{}])
    params.update(exogenous_data=[signals])
    params.update(backtesting_action_states=[past_action_states])

    # Update initial state for extrapolation
    initial_state.update(pid_state=initial_pid_state,
                         pid_params=initial_pid_params,
                         token_state=last_row.token_state,
                         eth_price=last_row.eth_price,
                         market_price=last_row.market_price) # TODO use test df state

    timesteps = N_t

    # Run extrapolation simulation
    sim_df = easy_run(initial_state,
                      params,
                      default_model.timestep_block,
                      timesteps,
                      1,
                      drop_substeps=True,
                      assign_params=False)

    # Clean-up
    sim_df = default_model.post_processing(sim_df)

    # TODO run notebook template

    return sim_df


def extrapolation_cycle() -> object:

    t1 = time()

    print("0. Preparing Data\n---")
    backtesting_df, governance_events = prepare()

    print("1. Backtesting Model\n---")
    backtest_results = backtest_model(backtesting_df, governance_events)

    print("2. Fitting Stochastic Processes\n---")
    stochastic_params = stochastic_fit(backtesting_df.exogenous_data)

    print("3. Extrapolating Exogenous Signals\n---")
    N_t = 240
    extrapolated_signals = extrapolate_signals(stochastic_params, N_t)

    print("4. Extrapolating Future Data\n---")
    future_data = extrapolate_data(extrapolated_signals,
                                   backtesting_df,
                                   backtest_results,
                                   governance_events,
                                   N_t)
    t2 = time()
    print(f"6. Done! {t2 - t1 :.2f}s\n---")

    return backtest_results, future_data


if __name__ == '__main__':
    extrapolation_cycle()

# %%
