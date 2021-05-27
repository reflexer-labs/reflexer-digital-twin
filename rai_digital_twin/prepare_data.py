import numpy as np
import pandas as pd
import json
import requests
from tqdm.auto import tqdm

from pandas.core.frame import DataFrame
from google.cloud import bigquery

from rai_digital_twin.types import ControllerState, GovernanceEvent, GovernanceEventKind, Height, Timestep, TokenState, BacktestingData


SUBGRAPH_URL = 'https://api.thegraph.com/subgraphs/name/reflexer-labs/rai-mainnet'


def retrieve_hourly_stats(block_numbers: list[int]) -> DataFrame:
    hourly = []
    for i in tqdm(block_numbers, desc='Retrieving hourly stats'):
        query = '''
        {
        hourlyStats(where: {blockNumber_gt: %s}) { 
            marketPriceUsd # price of COIN in USD (uni pool price * ETH median price)
            marketPriceEth # Price of COIN in ETH (uni pool price)
        }
        }
        ''' % i
        r = requests.post(SUBGRAPH_URL, json={'query': query})
        s = json.loads(r.content)['data']['hourlyStats'][0]
        hourly.append(s)
    hourlyStats = (pd.DataFrame(hourly)
                   .assign(block_number=block_numbers)
                   .set_index('block_number'))
    return hourlyStats


def retrieve_system_states(block_numbers: list[int]) -> DataFrame:
    state = []
    for i in tqdm(block_numbers, desc='Retrieving system states'):
        query = '''
        {
        systemState(block: {number:%s},id:"current") { 
            coinUniswapPair {
            label
            reserve0
            reserve1
            token0Price
            token1Price
            totalSupply
            }
            currentCoinMedianizerUpdate{
            value
            }
            currentRedemptionRate {
            eightHourlyRate
            annualizedRate
            hourlyRate
            createdAt
            }
            currentRedemptionPrice {
            value
            }
            erc20CoinTotalSupply
            globalDebt
            globalDebtCeiling
            safeCount,
            totalActiveSafeCount
            coinAddress
            wethAddress
            systemSurplus
            debtAvailableToSettle
            lastPeriodicUpdate
            createdAt
            createdAtBlock
        }
        }
        ''' % i
        r = requests.post(SUBGRAPH_URL, json={'query': query})
        s = json.loads(r.content)['data']['systemState']
        state.append(s)

    systemState = pd.DataFrame(state)
    systemState['block_number'] = block_numbers
    systemState = systemState.set_index('block_number')

    systemState['RedemptionRateAnnualizedRate'] = systemState.currentRedemptionRate.apply(
        lambda x: x['annualizedRate'])
    systemState['RedemptionRateHourlyRate'] = systemState.currentRedemptionRate.apply(
        lambda x: x['hourlyRate'])
    systemState['RedemptionRateEightHourlyRate'] = systemState.currentRedemptionRate.apply(
        lambda x: x['eightHourlyRate'])
    systemState['RedemptionPrice'] = systemState.currentRedemptionPrice.apply(
        lambda x: x['value'])
    systemState['EthInUniswap'] = systemState.coinUniswapPair.apply(
        lambda x: x['reserve1'])
    systemState['RaiInUniswap'] = systemState.coinUniswapPair.apply(
        lambda x: x['reserve0'])
    systemState['RaiDrawnFromSAFEs'] = systemState['erc20CoinTotalSupply']
    #systemState['RAIInUniswapV2(RAI/ETH)'] = systemState.coinUniswapPair.apply(lambda x: x['reserve0'])
    del systemState['currentRedemptionRate']
    del systemState['currentRedemptionPrice']

    systemState = systemState[['debtAvailableToSettle',
                               'globalDebt',
                               'globalDebtCeiling',
                               'systemSurplus',
                               'totalActiveSafeCount',
                               'RedemptionRateAnnualizedRate',
                               'RedemptionRateHourlyRate',
                               'RedemptionRateEightHourlyRate',
                               'RedemptionPrice',
                               'EthInUniswap',
                               'RaiInUniswap',
                               'RaiDrawnFromSAFEs']]
    return systemState


def retrieve_safe_history(block_numbers: list[int]) -> DataFrame:
    safehistories = []
    for i in tqdm(block_numbers, desc='Retrieving SAFEs History'):
        query = '''
        {
        safes(block: {number:%s}) {
                collateral
                debt
        }
        }
        ''' % i
        r = requests.post(SUBGRAPH_URL, json={'query': query})
        s = json.loads(r.content)['data']['safes']
        t = pd.DataFrame(s)
        t['collateral'] = t['collateral'].astype(float)
        t['debt'] = t['debt'].astype(float)
        safehistories.append(pd.DataFrame(t.sum().to_dict(), index=[0]))

    safe_history = (pd.concat(safehistories)
                    .assign(block_number=block_numbers)
                    .set_index('block_number')
                    )
    return safe_history


def retrieve_eth_price() -> DataFrame:
    # SQL query
    sql = """
    SELECT 
    * 
    FROM `blockchain-etl.ethereum_rai.OSM_event_UpdateResult`
    ORDER By block_timestamp DESC

    """
    constant = 1000000000000000000
    client = bigquery.Client()
    raw_df = client.query(sql).to_dataframe()
    eth_price_OSM = raw_df
    eth_price_OSM['ETH Price (OSM)'] = eth_price_OSM['newMedian'].astype(
        float)/constant
    eth_price_OSM = eth_price_OSM[[
        'block_number', 'eth_price', 'block_timestamp']]
    return eth_price_OSM.set_index("block_number")


def download_data() -> DataFrame:
    eth_price_df = retrieve_eth_price()
    block_numbers = eth_price_df.index
    dfs = (retrieve_system_states(block_numbers),
           retrieve_hourly_stats(block_numbers),
           retrieve_safe_history(block_numbers),
           eth_price_df)
    historical_df = pd.concat(dfs, join='inner')

    return historical_df


def row_to_controller_state(row: pd.Series) -> ControllerState:
    return ControllerState(row.RedemptionPrice,
                           row.RedemptionRateHourlyRate,
                           np.nan,
                           np.nan)


def row_to_token_state(row: pd.Series) -> TokenState:
    return TokenState(row.RaiInUniswap,
                      row.EthInUniswap,
                      row.debt,
                      row.collateral)


def extract_exogenous_data(df: pd.DataFrame) -> dict[Timestep, dict[str, float]]:
    """
    Extract exogenous variables from historical dataframe.
    """
    EXOGENOUS_MAP = {'ETH Price (OSM)': 'eth_price',
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
    # TODO: Parametrize start and end dates
    df = (pd.read_csv(path)
            .sort_values('block_number', ascending=True)
            .iloc[100:]  # HACK
            .iloc[-500:]  # HACK
            .reset_index(drop=True)
            .assign(RedemptionRateHourlyRate=lambda df: df.RedemptionRateHourlyRate))
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


def interpolate_timestep(heights_per_timesteps: list[Height],
                         height_to_interpolate: Height) -> Timestep:
    """
    Note: heights per timestep must be ordered
    """
    last_timestep = 0
    for (_, height) in enumerate(heights_per_timesteps):
        if height_to_interpolate >= height:
            last_timestep += 1
        else:
            continue
    return last_timestep


def parse_raw_events(raw_events: list[dict],
                     heights: dict[Timestep, Height]) -> dict[Timestep, GovernanceEvent]:
    # Map the raw events into (Timestep, GovernanceEvent) relations
    height_list = list(heights.values())
    events = {}
    for raw_event in raw_events:
        event = GovernanceEvent(GovernanceEventKind.change_pid_params,
                                raw_event)
        timestep = interpolate_timestep(
            height_list, int(raw_event['eth_block']))
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
