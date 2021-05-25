
from rai_digital_twin.types import BacktestingData, ControllerParams, ControllerState
import pandas as pd
from typing import Dict, List

from cadCAD_tools import easy_run
from .backtesting import simulation_loss
from .prepare_data import load_backtesting_data, load_governance_events
from .stochastic import FitParams, fit_eth_price, fit_predict_eth_price, generate_eth_samples
from rai_digital_twin import default_model

BACKTESTING_DATA_PATH = 'data/states.csv'
GOVERNANCE_EVENTS_PATH = 'data/controller_params.csv'


def save_artifact():
    return None


def retrieve_historical_data() -> pd.DataFrame:
    pass


def prepare(report_path: str = None):
    """
    Retrieves all required historical and prior data.
    """
    backtesting_data = load_backtesting_data(BACKTESTING_DATA_PATH)

    governance_events = load_governance_events(GOVERNANCE_EVENTS_PATH,
                                               backtesting_data.heights)

    return (backtesting_data, governance_events)


def backtest_model(backtesting_data: BacktestingData,
                   governance_events) -> None:

    initial_state = default_model.initial_state

    initial_pid_state = ControllerState(backtesting_data.pid_states[0].redemption_price,
                                        backtesting_data.pid_states[0].redemption_rate,
                                        0.0,
                                        0.0)
    initial_state.update(pid_state=initial_pid_state,
                         token_state=backtesting_data.token_states[0])

    params = default_model.parameters
    params.update(heights=[backtesting_data.heights])
    params.update(governance_events=[governance_events])
    params.update(backtesting_data=[backtesting_data.token_states])
    params.update(exogenous_data=[backtesting_data.exogenous_data])

    timesteps = len(backtesting_data.heights) - 1

    sim_df = easy_run(initial_state,
                      params,
                      default_model.timestep_block,
                      timesteps,
                      1,
                      drop_substeps=True,
                      assign_params=False)

    sim_df = default_model.post_processing(sim_df)
    test_df = pd.DataFrame.from_dict(
        backtesting_data.pid_states, orient='index')
    loss = simulation_loss(sim_df, test_df)
    print(f"Backtesting loss: {loss :.2%}")

    return (sim_df, test_df)


def stochastic_fit(input_data: object,
                   report_path: str = None) -> dict:
    """
    Acquire parameters for the stochastic input signals.
    """

    X = pd.DataFrame(input_data).T.eth_price
    params = fit_eth_price(X)
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
    return exogenous_data


def extrapolate_data(signals: object,
                     backtesting_data,
                     backtest_results,
                     governance_events,
                     N_t: int,
                     report_path: str = None) -> object:
    """
    Generate a extrapolation dataset.
    """

    # Index for the last available data points
    last_t = len(backtesting_data.heights) - 1
    last_row = backtest_results[0].iloc[-1]

    seconds_per_timesteps = (60 * 60)
    heights = {i: i * seconds_per_timesteps for i in range(N_t)}

    initial_state = default_model.initial_state
    initial_pid_state = ControllerState(backtesting_data.pid_states[last_t].redemption_price,
                                        backtesting_data.pid_states[last_t].redemption_rate,
                                        0.0,
                                        0.0)
    initial_pid_params = ControllerParams(last_row.kp,
                                          last_row.ki,
                                          last_row.leaky_factor,
                                          last_row.period,
                                          last_row.enabled)
    initial_state.update(pid_state=initial_pid_state,
                         pid_params=initial_pid_params,
                         token_state=backtesting_data.token_states[last_t])

    params = default_model.parameters
    params.update(heights=[None])
    params.update(backtesting_data=[None])
    params.update(governance_events=[{}])
    params.update(exogenous_data=[signals])

    timesteps = len(backtesting_data.heights) - 1

    sim_df = easy_run(initial_state,
                      params,
                      default_model.timestep_block,
                      timesteps,
                      1,
                      drop_substeps=True,
                      assign_params=False)

    sim_df = default_model.post_processing(sim_df)

    return sim_df


def extrapolation_cycle() -> object:

    print("0. Preparing Data\n---")
    backtesting_df, governance_events = prepare()
    print("1. Backtesting Model\n---")
    backtest_results = backtest_model(backtesting_df, governance_events)
    print("2. Fitting Stochastic Processes\n---")
    stochastic_params = stochastic_fit(backtesting_df.exogenous_data)
    print("3. Extrapolating Exogenous Signals\n---")
    N_t = 100
    extrapolated_signals = extrapolate_signals(stochastic_params, N_t)
    print("4. Extrapolating Future Data\n---")
    future_data = extrapolate_data(extrapolated_signals,
                                   backtesting_df,
                                   backtest_results,
                                   governance_events,
                                   N_t)
    print("6. Done!\n---")
    return future_data


if __name__ == '__main__':
    extrapolation_cycle()

# %%
