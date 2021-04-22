from typing import Callable
import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame


from rai_digital_twin.models.digital_twin_v1.model.types import *

import rai_digital_twin.models.options as options
from rai_digital_twin.models.constants import SPY, RAY

from rai_digital_twin.models.digital_twin_v1.model.state_variables.system import stability_fee
from rai_digital_twin.models.digital_twin_v1.model.state_variables.historical_state import eth_price_df, liquidity_demand_df, token_swap_df


'''
See https://medium.com/reflexer-labs/introducing-proto-rai-c4cf1f013ef for current/launch values
'''


class ReflexerModelParameters(TypedDict):
    debug: bool
    raise_on_assert: bool
    free_memory_states: List[str]
    IntegralType: object
    # IntegralType
    eth_price: Callable[[Run, Timestep], List[USD_per_ETH]]
    liquidity_demand_events: Callable[[Run, Timestep, DataFrame], exaRAI]
    token_swap_events: Callable[[Run, Timestep, DataFrame], exaRAI]
    seconds_passed: Callable[[Timestep, DataFrame], Seconds]
    liquidity_demand_enabled: bool
    liquidity_demand_shock: bool
    liquidity_demand_max_percentage: Percentage
    liquidity_demand_shock_percentage: Percentage
    expected_blocktime: Seconds
    control_period: Seconds
    controller_enabled: bool
    enable_controller_time: Seconds
    kp: Per_USD
    ki: Per_USD_Seconds
    alpha: Per_RAY
    error_term: Callable[[USD_per_RAI, USD_per_RAI], USD_per_RAI]
    rescale_target_price: bool
    arbitrageur_considers_liquidation_ratio: bool
    interest_rate: float
    beta_1: USD_per_ETH
    beta_2: USD_per_RAI
    liquidation_ratio: Percentage
    liquidation_buffer: Percentage
    liquidation_penalty: Percentage
    debt_ceiling: RAI
    stability_fee: Callable[[Timestep, DataFrame],  Percentage_Per_Second]
    uniswap_fee: Percentage
    gas_price: ETH
    swap_gas_used: Gwei
    cdp_gas_used: Gwei



params = {
    # Admin parameters
    'debug': [False], # Print debug messages (see APT model)
    'raise_on_assert': [True], # See assert_log() in utils.py
    'free_memory_states': [['events', 'cdps', 'uniswap_oracle']],

    # Configuration options
    options.IntegralType.__name__: [options.IntegralType.LEAKY.value],

    # Exogenous states, loaded as parameter at every timestep - these are lambda functions, and have to be called
    'eth_price': [lambda run, timestep, df=eth_price_df: df[str(run-1)].iloc[timestep]],
    'liquidity_demand_events': [lambda run, timestep, df=liquidity_demand_df: df[str(run-1)].iloc[timestep]],
    'token_swap_events': [lambda run, timestep, df=token_swap_df: df[str(run-1)].iloc[timestep]],
    'seconds_passed': [lambda timestep, df=None: 3600],
    
    'liquidity_demand_enabled': [True], # turn on or off all shocks
    'liquidity_demand_shock': [False], # introduce shocks (up to 50% of secondary market pool)
    'liquidity_demand_max_percentage': [0.1], # max percentage of secondary market pool when no shocks introduced using liquidity_demand_shock
    'liquidity_demand_shock_percentage': [0.5], # max percentage of secondary market pool when shocks introduced using liquidity_demand_shock

    # Time parameters
    'expected_blocktime': [15], # seconds
    'control_period': [3600 * 4], # seconds; must be multiple of cumulative time
    
    # Controller parameters
    'controller_enabled': [True],
    'enable_controller_time': [7 * 24 * 3600], # delay in enabling controller (7 days)
    'kp': [2e-7], # proportional term for the stability controller: units 1/USD
    'ki': [-5e-9], # integral term for the stability controller scaled by control period: units 1/(USD*seconds)
    'alpha': [.999 * RAY], # in 1/RAY
    'error_term': [lambda target, measured: target - measured],
    'rescale_target_price': [True], # scale the target price by the liquidation ratio
    
    # APT model
    'arbitrageur_considers_liquidation_ratio': [True],
    'interest_rate': [1.03], # Real-world expected interest rate, for determining profitable arbitrage opportunities

    # APT OLS model
    # OLS values (Feb. 6, 2021) for beta_1 and beta_2
    'beta_1': [9.084809e-05],
    'beta_2': [-4.194794e-08],

    # CDP parameters
    'liquidation_ratio': [1.45], # Configure the liquidation ratio parameter e.g. 150%
    'liquidation_buffer': [2.0], # Configure the liquidation buffer parameter: the multiplier for the liquidation ratio, that users apply as a buffer
    'liquidation_penalty': [0], # Percentage added on top of collateral needed to liquidate CDP. This is needed in order to avoid auction grinding attacks.
    'debt_ceiling': [1e9],

    # System parameters
    'stability_fee': [lambda timestep, df=None: stability_fee], # per second interest rate (x% per month)

    # Uniswap parameters
    'uniswap_fee': [0.003], # 0.3%
    'gas_price': [100e-9], # 100 gwei, current "fast" transaction
    'swap_gas_used': [103834],
    'cdp_gas_used': [(369e3 + 244e3) / 2], # Deposit + borrow; repay + withdraw
}



# Assert that the dict is consistent
typed_dict_keys = set(ReflexerModelParameters.__annotations__.keys())
state_var_keys = set(params.keys())
assert typed_dict_keys == state_var_keys, (state_var_keys - typed_dict_keys, typed_dict_keys - state_var_keys)