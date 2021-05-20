
from rai_digital_twin.types import BacktestingData, ControllerState
import pandas as pd
from typing import Dict, List

from cadCAD_tools import easy_run
from .backtesting import simulation_loss
from .prepare_data import load_backtesting_data, load_governance_events
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
    pass


def estimate_parameters(input_data: object,
                        report_path: str = None) -> dict:
    """
    Acquire parameters for the model simulation/
    """
    pass


def extrapolate_signals(signal_params: object,
                        report_path: str = None) -> object:
    """
    Generate input signals from given parameters.
    """
    pass


def extrapolate_data(signals: object,
                     params: object,
                     report_path: str = None) -> object:
    """
    Generate a extrapolation dataset.
    """
    pass


def extrapolation_cycle() -> object:

    backtesting_df, governance_events = prepare()
    backtest_model(backtesting_df, governance_events)
    fit_parameters = stochastic_fit(historical_df)
        # estimated_params = estimate_parameters(historical_df)


    # extrapolated_signals = extrapolate_signals(fit_parameters)

    # extrapolated_data = extrapolate_data(
    #     extrapolated_signals, estimated_params)
    # return extrapolated_data


if __name__ == '__main__':
    extrapolation_cycle()

# %%
