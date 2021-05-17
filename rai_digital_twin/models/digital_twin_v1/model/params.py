from typing import Union
from cadCAD_tools.types import Param, ParamSweep
from cadCAD_tools.preparation import prepare_params
from rai_digital_twin.types import USD_per_ETH, Seconds, Per_USD, RAI, ETH
from rai_digital_twin.types import Percentage, Gwei, Per_USD_Seconds
from rai_digital_twin.models.constants import RAY

ETH_PRICE_SERIES: list[float] = []
SECONDS_PER_TIMESTEP: Seconds = 3600
CONTROL_PERIOD: Seconds = 4 * 60 * 60

raw_params: dict[str, Union[Param, ParamSweep]] = {
    # Exogenous states, loaded as parameter at every timestep - these are lambda functions, and have to be called
    'eth_price': Param(ETH_PRICE_SERIES, list[USD_per_ETH]),
    'seconds_passed': Param(SECONDS_PER_TIMESTEP, Seconds),

    # Time parameters
    'expected_blocktime': Param(15, Seconds),
    # must be multiple of cumulative time
    'control_period': Param(CONTROL_PERIOD, Seconds),

    # Controller parameters
    # Proportional term
    'kp': Param(2e-7, Per_USD),
    # Integral term scaled by control period
    'ki': Param(-5e-9, Per_USD_Seconds), 
    # Leaky integral term
    'alpha': Param(0.999, Percentage), 
}

params = prepare_params(raw_params)
