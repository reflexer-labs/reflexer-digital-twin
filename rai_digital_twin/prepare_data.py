import numpy as np
import pandas as pd
import json
from rai_digital_twin.types import ControllerState, GovernanceEvent, GovernanceEventKind, Height, Timestep, TokenState, BacktestingData


def row_to_controller_state(row: pd.Series) -> ControllerState:
    return ControllerState(row.RedemptionPrice,
                           row.RedemptionRateHourlyRate,
                           np.nan,
                           np.nan)


def row_to_token_state(row: pd.Series) -> TokenState:
    return TokenState(row.RaiInUniswap,
                      row.RaiInUniswap,
                      row.debt,
                      row.collateral)


def extract_exogenous_data(df: pd.DataFrame) -> dict[Timestep, dict[str, float]]:
    """
    Extract exogenous variables from historical dataframe.
    """
    EXOGENOUS_MAP = {'marketPriceEth': 'eth_price',
                     'marketPriceUsd': 'market_price'}

    exogenous_data = (df.loc[:, EXOGENOUS_MAP.keys()]
                      .rename(columns=EXOGENOUS_MAP)
                      .to_dict(orient='index'))
    return exogenous_data


def load_backtesting_data(path: str) -> BacktestingData:
    """
    Make the historical clean for backtesting.
    """
    # Load CSV file
    df = (pd.read_csv(path)
            .sort_values('block_number', ascending=True)
            .head(100) # HACK
            .reset_index(drop=True)
            .assign(marketPriceEth=lambda df: 1 / df.marketPriceEth)
            .assign(RedemptionRateHourlyRate= lambda df: df.RedemptionRateHourlyRate - 1))
    # Retrieve historical info
    token_states = df.apply(row_to_token_state, axis=1).to_dict()
    exogenous_data = extract_exogenous_data(df)
    heights = df.block_number.to_dict()
    pid_states = df.apply(row_to_controller_state, axis=1).to_dict()

    # Output
    return BacktestingData(token_states, exogenous_data, heights, pid_states)


def retrieve_raw_events(params_df: pd.DataFrame,
                        initial_height: Height) -> list[dict]:
    first_event = None
    raw_events = []
    for event in params_df:
        eth_block = event['eth_block']
        if eth_block < initial_height:
            first_event = event
        elif eth_block >= initial_height:
            raw_events.append(event)
    raw_events.insert(0, first_event)
    return raw_events


def interpolate_timestep(heights_per_timesteps: dict[Timestep, Height],
                         height_to_interpolate: Height) -> Timestep:
    """
    Note: heights per timestep must be ordered
    """
    for (timestep, height) in heights_per_timesteps.items():
        if height_to_interpolate < height:
            return timestep
        else:
            continue
    return -1
            

def parse_raw_events(raw_events: list[dict],
                     heights: dict[Timestep, Height]) -> dict[Timestep, GovernanceEvent]:
    # Map the raw events into (Timestep, GovernanceEvent) relations
    events = {}
    for raw_event in raw_events:
        event = GovernanceEvent(GovernanceEventKind.change_pid_params,
                                raw_event)
        timestep = interpolate_timestep(heights, raw_event['eth_block'])
        if timestep >= 0:
            timestep = int(timestep)
            events[timestep] = event
        else:
            continue
    return events


def load_governance_events(path: str,
                           heights: dict[Timestep, Height]) -> dict[Timestep, GovernanceEvent]:

    params_df = pd.read_csv(path).sort_values(
        'eth_block').to_dict(orient='records')
    initial_height = list(heights.values())[0]
    raw_events = retrieve_raw_events(params_df, initial_height)
    events = parse_raw_events(raw_events, heights)
    return events


def download_past_data():
    pass
