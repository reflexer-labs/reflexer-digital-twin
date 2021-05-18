import numpy as np
import pandas as pd
import json
from rai_digital_twin.types import ControllerState, GovernanceEvent, Timestep, TokenState, BacktestingData


def row_to_controller_state(row: pd.Series) -> ControllerState:
    return ControllerState(row.RedemptionPrice,
                           row.RedemptionRateAnnualizedRate,
                           np.nan,
                           np.nan)


def row_to_token_state(row: pd.Series) -> TokenState:
    return TokenState(row.RaiInUniswap,
                      row.RaiInUniswap,
                      row.debt,
                      row.collateral)


def extract_exogenous_data(df: pd.DataFrame) -> list[dict[str, float]]:
    EXOGENOUS_MAP = {'marketPriceEth': 'eth_price',
                  'marketPriceUsd': 'market_price'}

    exogenous_data = (df.loc[:, EXOGENOUS_MAP.keys()]
                    .rename(columns=EXOGENOUS_MAP)
                    .to_dict(orient='records'))
    return exogenous_data
            

def parse_backtesting_data(path: str) -> BacktestingData:
    df = pd.read_csv(path)
    pid_states = df.apply(row_to_controller_state, axis=1).tolist()
    token_states = df.apply(row_to_token_state, axis=1).tolist()
    exogenous_data = extract_exogenous_data(df)
    return BacktestingData(token_states, exogenous_data, pid_states)


def parse_governance_events(path: str) -> dict[Timestep, GovernanceEvent]:
    with open(path, 'r') as fid:
        raw_events: list = json.load(fid)

    events = {}
    for raw_event in raw_events:
        event = parse_event(raw_event)
    return {}

def download_past_data():
    pass