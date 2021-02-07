import numpy as np
import pandas as pd

import models.options as options
from models.constants import SPY, RAY

from models.system_model_v3.model.state_variables.system import stability_fee
from models.system_model_v3.model.state_variables.historical_state import eth_price_df, liquidity_demand_df, token_swap_df


'''
See https://medium.com/reflexer-labs/introducing-proto-rai-c4cf1f013ef for current/launch values
'''

# TODO: Default assumption, set according to process for deriving per-second alpha
halflife = SPY / 52 # weeklong halflife
alpha = int(np.power(.5, float(1 / halflife)) * RAY)

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
    'liquidity_demand_shock': [False], # introduce shocks (up to 50% of secondary market pool)
    'liquidity_demand_max_percentage': [0.1], # max percentage of secondary market pool when no shocks introduced using liquidity_demand_shock
    'liquidity_demand_shock_percentage': [0.5], # max percentage of secondary market pool when shocks introduced using liquidity_demand_shock

    # Time parameters
    'expected_blocktime': [15], # seconds
    'control_period': [3600 * 3], # seconds; must be multiple of cumulative time
    
    # Controller parameters
    'controller_enabled': [False],
    'enable_controller_time': [7 * 24 * 3600], # after 7 days
    'kp': [5e-7], # proportional term for the stability controller: units 1/USD
    'ki': [-1e-7], # integral term for the stability controller scaled by control period: units 1/(USD*seconds)
    'alpha': [alpha], # in 1/RAY
    'error_term': [lambda target, measured: target - measured],
    'rescale_target_price': [True], # scale the target price by the liquidation ratio
    
    # APT model
    'arbitrageur_considers_liquidation_ratio': [True],
    'interest_rate': [1.03], # Real-world expected interest rate, for determining profitable arbitrage opportunities
    # 'eth_price_mean': [eth_price_mean],
    # 'eth_returns_mean': [eth_returns_mean],
    # 'market_price_mean': [market_price_mean],

    # APT OLS model
    # OLS values (Feb. 6, 2021) for beta_1 and beta_2
    'beta_1': [9.084809e-05],
    'beta_2': [-4.194794e-08],

    # CDP parameters
    'liquidation_ratio': [1.5], # Configure the liquidation ratio parameter e.g. 150%
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
