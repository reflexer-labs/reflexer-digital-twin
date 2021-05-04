from typing import Dict, TypedDict
import pandas as pd
from rai_digital_twin.models.digital_twin_v1.model.state_variables.liquidity import cdps, eth_collateral, principal_debt, uniswap_rai_balance, uniswap_eth_balance
from rai_digital_twin.models.digital_twin_v1.model.state_variables.system import stability_fee, redemption_price
from rai_digital_twin.types import *
import datetime as dt

class ReflexerStateVariables(TypedDict, total=True):
    """
    Units and types of the state variables
    """
    # Metadata / metrics
    cdp_metrics: CDP_Metric

    # Time states
    timedelta: Seconds
    cumulative_time: Seconds
    timestamp: dt.datetime
    blockheight: Height

    # Exogenous states
    eth_price: USD_per_ETH

    # CDP states
    cdps: pd.DataFrame

    # ETH collateral states
    eth_collateral: ETH
    eth_locked: ETH
    eth_freed: ETH
    eth_bitten: ETH

    # Principal debt states
    principal_debt: RAI
    rai_drawn: RAI
    rai_wiped: RAI
    rai_bitten: RAI

    # Accrued interest states
    accrued_interest: RAI
    interest_bitten: RAI
    w_1: RAI
    w_2: RAI
    w_3: RAI
    system_revenue: RAI

    # System states
    stability_fee: Percentage_Per_Second
    market_price_twap: USD_per_RAI
    redemption_price: USD_per_RAI
    redemption_rate: Percentage_Per_Second

    # Controller states
    error_star: USD_per_RAI
    error_star_integral: USD_Seconds_per_RAI

    # Uniswap states
    market_slippage: Percentage   
    RAI_balance: RAI
    ETH_balance: ETH


# NB: These initial states may be overriden in the relevant notebook or experiment process
state_variables = {
    # Metadata / metrics
    'cdp_metrics': {},
    
    # Time states
    'timedelta': 0, # seconds
    'cumulative_time': 0, # seconds
    'timestamp': dt.datetime.strptime('2017-01-01', '%Y-%m-%d'), # type: datetime; start time
    'blockheight': 0, # block offset (init 0 simplicity)
    
    # Exogenous states
    'eth_price': None, # unit: dollars; updated from historical data as exogenous parameter
    
    # CDP states
    'cdps': cdps, # A dataframe of CDPs (both open and closed)

    # ETH collateral states
    'eth_collateral': eth_collateral, # Total ETH collateral in the CDP system i.e. locked - freed - bitten
    'eth_locked': eth_collateral, # Total ETH locked into CDPs
    'eth_freed': 0, # Total ETH freed from CDPs
    'eth_bitten': 0, # Total ETH bitten/liquidated from CDPs
    
    # Principal debt states
    'principal_debt': principal_debt, # "D_1"; the total debt in the CDP system i.e. drawn - wiped - bitten
    'rai_drawn': principal_debt, # total RAI debt minted from CDPs
    'rai_wiped': 0, # total RAI debt wiped/burned from CDPs in repayment
    'rai_bitten': 0, # total RAI liquidated from CDPs
    
    # Accrued interest states
    'accrued_interest': 0, # "D_2"; the total interest accrued in the system i.e. current D_2 + w_1 - w_2 - w_3
    'interest_bitten': 0, # cumulative w_3
    'w_1': 0, # discrete "drip" event, in RAI
    'w_2': 0, # discrete "shut"/"wipe" event, in RAI
    'w_3': 0, # discrete "bite" event, in RAI
    'system_revenue': 0, # "R"; value accrued by protocol token holders as result of contracting supply
    
    # System states
    'stability_fee': stability_fee, # interest rate used to calculate the accrued interest; per second interest rate (1.5% per month)
    'market_price_twap': 0,
    'redemption_price': redemption_price, # unit: dollars; equivalent to redemption price
    'redemption_rate': 0 / (30 * 24 * 3600), # per second interest rate (X% per month), updated by controller
    
    # Controller states
    'error_star': 0, # price units
    'error_star_integral': 0, # price units x seconds
    
    # Uniswap states
    'market_slippage': 0,
    'RAI_balance': uniswap_rai_balance,
    'ETH_balance': uniswap_eth_balance
}

# Assert that the dict is consistent
typed_dict_keys = set(ReflexerStateVariables.__annotations__.keys())
state_var_keys = set(state_variables.keys())
assert typed_dict_keys == state_var_keys, (state_var_keys - typed_dict_keys, typed_dict_keys - state_var_keys)