import pandas as pd
from typing import Dict, List

from cadCAD_tools import easy_run
from .backtesting import simulation_loss

from rai_digital_twin import default_model


def save_artifact():
    return None

def retrieve_historical_data() -> pd.DataFrame:
    pass


def prepare(report_path: str = None) -> dict:
    """
    Retrieves all required historical and prior data.
    """
    input_data = {}
    input_data['historical_data'] = retrieve_historical_data()
    return input_data


def backtest_model(historical_data: pd.DataFrame) -> None:


    initial_exogenous_data = exogenous_data.iloc[0]

    params = default_model.parameters
    params.update(governance_events=governance_events)
    params.update(backtesting_data=token_states)
    params.update(exogenous_data=exogenous_data)


    partial_state_update_blocks = default_model.timestep_block
    timesteps = len(historical_data)

    sim_df = easy_run(default_model.initial_state,
                      params,
                      default_model.timestep_block,
                      timesteps,
                      1)

    test_df = None

    loss = simulation_loss(sim_df, test_df)

    return None


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

    input_data = prepare()

    historical_df = input_data['historical_data']

    backtest_model(historical_df)
    estimated_params = estimate_parameters(historical_df)
    fit_parameters = stochastic_fit(historical_df)

    extrapolated_signals = extrapolate_signals(fit_parameters)
    
    extrapolated_data = extrapolate_data(
        extrapolated_signals, estimated_params)
    return extrapolated_data


if __name__ == '__main__':
    extrapolation_cycle()