from rai_digital_twin.types import *

from rai_digital_twin.models.constants import RAY

ETH_PRICE_SERIES: List[float] = []
SECONDS_PER_TIMESTEP = 3600


params: Dict[str, Param] = {
    # Admin parameters
    'raise_on_assert': Param(True, bool),  # See assert_log() in utils.py

    # Exogenous states, loaded as parameter at every timestep - these are lambda functions, and have to be called
    'eth_price': Param(ETH_PRICE_SERIES, List[USD_per_ETH]),
    'seconds_passed': Param(SECONDS_PER_TIMESTEP, Seconds),

    # Time parameters
    'expected_blocktime': Param(15, Seconds),
    # must be multiple of cumulative time
    'control_period': Param(SECONDS_PER_TIMESTEP * 4, Seconds),

    # Controller parameters
    # proportional term for the stability controller: units 1/USD
    'kp': Param(2e-7, Per_USD),
    # integral term for the stability controller scaled by control period: units 1/(USD*seconds)
    'ki': Param(-5e-9, Per_USD_Seconds),
    'alpha': Param(.999 * RAY, Per_RAY),  # in 1/RAY
    # scale the redemption price by the liquidation ratio
    'rescale_redemption_price': Param(True, bool),

    # CDP parameters
    # Configure the liquidation ratio parameter e.g. 150%
    'liquidation_ratio': Param(1.45, Percentage),
    # Configure the liquidation buffer parameter: the multiplier for the liquidation ratio, that users apply as a buffer
    'liquidation_buffer': Param(2.0, Percentage),
    # Percentage added on top of collateral needed to liquidate CDP. This is needed in order to avoid auction grinding attacks.
    'liquidation_penalty': Param(0, Percentage),
    'debt_ceiling': Param(1e9, RAI),

    # Uniswap parameters
    'uniswap_fee': Param(0.003, Percentage),  # 0.3%
    'gas_price': Param(100e-9, ETH),  # 100 gwei, current "fast" transaction
    'swap_gas_used': Param(103834, Gwei),
    # Deposit + borrow; repay + withdraw
    'cdp_gas_used': Param((369e3 + 244e3) / 2, Gwei),
}

simple_params = {k: [v.value]
                 for k, v in params.items()
                 if type(v) is Param}

sweep_params = {k: v.value
                for k, v in params.items()
                if type(v) is ParamSweep}

params = {**simple_params, **sweep_params}
