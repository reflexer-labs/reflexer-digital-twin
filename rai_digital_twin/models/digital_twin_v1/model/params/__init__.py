from typing import Callable
import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame


from rai_digital_twin.types import *

import rai_digital_twin.models.options as options
from rai_digital_twin.models.constants import SPY, RAY

from rai_digital_twin.models.digital_twin_v1.model.state_variables.system import stability_fee


'''
See https://medium.com/reflexer-labs/introducing-proto-rai-c4cf1f013ef for current/launch values
'''


class ReflexerModelParameters(TypedDict):
    raise_on_assert: bool
    IntegralType: object
    # IntegralType
    eth_price: Callable[[Run, Timestep], List[USD_per_ETH]]
    seconds_passed: Callable[[Timestep, DataFrame], Seconds]
    expected_blocktime: Seconds
    control_period: Seconds
    kp: Per_USD
    ki: Per_USD_Seconds
    alpha: Per_RAY
    rescale_redemption_price: bool
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

ETH_PRICE_SERIES = []
SECONDS_PER_TIMESTEP = 3600

params = {
    # Admin parameters
    'raise_on_assert': [True], # See assert_log() in utils.py

    # Configuration options
    options.IntegralType.__name__: [options.IntegralType.LEAKY.value],

    # Exogenous states, loaded as parameter at every timestep - these are lambda functions, and have to be called
    'eth_price': [ETH_PRICE_SERIES],
    'seconds_passed': [SECONDS_PER_TIMESTEP],
    
    # Time parameters
    'expected_blocktime': [15], # seconds
    'control_period': [SECONDS_PER_TIMESTEP * 4], # seconds; must be multiple of cumulative time
    
    # Controller parameters
    'kp': [2e-7], # proportional term for the stability controller: units 1/USD
    'ki': [-5e-9], # integral term for the stability controller scaled by control period: units 1/(USD*seconds)
    'alpha': [.999 * RAY], # in 1/RAY
    'rescale_redemption_price': [True], # scale the redemption price by the liquidation ratio

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
    'stability_fee': [stability_fee], # per second interest rate (x% per month)

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