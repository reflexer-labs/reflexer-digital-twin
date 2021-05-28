import json
import requests
from tqdm.auto import tqdm
from pandas.core.frame import DataFrame
from google.cloud import bigquery
from typing import Iterable
import pandas as pd

PRAI_SUBGRAPH_URL = 'https://api.thegraph.com/subgraphs/name/reflexer-labs/prai-mainnet'
RAI_SUBGRAPH_URL = 'https://api.thegraph.com/subgraphs/name/reflexer-labs/rai-mainnet'

def yield_hourly_stats() -> Iterable[dict]:
    query_header = '''
    query {{
        hourlyStats(first: 1000, skip:{}) {{'''
    query_tail = '''    
    }
    }'''
    query_body = '''
        timestamp
        blockNumber
        marketPriceUsd # price of COIN in USD (uni pool price * ETH median price)
        marketPriceEth # Price of COIN in ETH (uni pool price)
    '''
    n = 0
    while True:
        query = query_header.format(n*1000) + query_body + query_tail
        r = requests.post(RAI_SUBGRAPH_URL, json={'query': query})
        s = json.loads(r.content)['data']['hourlyStats']
        n += 1
        if len(s) < 1:
            break
        yield s


def retrieve_hourly_stats() -> DataFrame:
    # Retrieve all hourly stats batches and transform into a single list of dicts
    gen_expr = (iter_hourly for
                iter_hourly
                in tqdm(yield_hourly_stats(),
                        desc='Retrieving hourly stats'))
    hourly_records: list[dict] = sum(gen_expr, [])

    # Clean-up to a pandas data frame
    hourlyStats = (pd.DataFrame
                   .from_records(hourly_records)
                   .applymap(pd.to_numeric)
                   .assign(timestamp=lambda df: pd.to_datetime(df.timestamp, unit='s'))
                   .assign(eth_price=lambda df: df.marketPriceUsd / df.marketPriceEth)
                   .set_index('blockNumber')
                   )
    hourlyStats.index.name = 'block_number'
    return hourlyStats


def retrieve_system_states(block_numbers: list[int]) -> DataFrame:
    state = []
    for i in tqdm(block_numbers, desc='Retrieving System States'):
        query = '''
        {
      systemState(block: {number:%s},id:"current") { 
        coinUniswapPair {
          reserve0
          reserve1
          token0Price
          token1Price
          totalSupply
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
        r = requests.post(PRAI_SUBGRAPH_URL, json={'query': query})
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
        r = requests.post(RAI_SUBGRAPH_URL, json={'query': query})
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


def retrieve_eth_price(limit=None,
                       date_range=None) -> DataFrame:

    if limit is not None:
        limit_subquery = f'LIMIT {limit}'
    else:
        limit_subquery = ''

    if date_range is not None:
        range_subquery = f"WHERE block_timestamp >= '{date_range[0]}' AND block_timestamp < '{date_range[1]}'"
    else:
        range_subquery = ''

    # BUG It seems that the OSM_event_UpdateResult has no updates since 2021-05-07
    sql = f"""
    SELECT 
    * 
    FROM `blockchain-etl.ethereum_rai.OSM_event_UpdateResult`
    {range_subquery}
    ORDER By block_timestamp DESC
    {limit_subquery}
    """

    constant = 1000000000000000000
    client = bigquery.Client()
    raw_df = client.query(sql).to_dataframe()
    eth_price_OSM = raw_df
    eth_price_OSM['eth_price'] = eth_price_OSM['newMedian'].astype(
        float)/constant
    eth_price_OSM = eth_price_OSM[[
        'block_number', 'eth_price', 'block_timestamp']]
    return eth_price_OSM.set_index("block_number")


def download_data(limit=None,
                  date_range=None) -> DataFrame:
    """
    Retrieve all historical data required for backtesting & extrapolation
    """
    # Get hourly stats from The Graph
    hourly_stats = retrieve_hourly_stats()

    # Filter hourly date if requested, else, use everything
    if date_range is not None:
        QUERY = f'timestamp >= "{date_range[0]}" & timestamp < "{date_range[1]}"'
        hourly_stats = hourly_stats.query(QUERY)
    else:
        pass

    # Get the first hourly results if requested
    if limit is not None:
        hourly_stats = hourly_stats.head(limit)
    else:
        pass

    # Retrieve block numbers
    block_numbers = hourly_stats.index
    
    # Get associated system states & safe state for each block numbers
    dfs = (retrieve_system_states(block_numbers),
           retrieve_safe_history(block_numbers),
           hourly_stats)

    # Join everything together
    historical_df = pd.concat(dfs, join='inner', axis=1)

    # Return Data Frame
    return historical_df.reset_index(drop=False)
