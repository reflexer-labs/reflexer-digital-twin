from typing import Union
from cadCAD_tools.types import Param, ParamSweep
from cadCAD_tools.preparation import prepare_params
from rai_digital_twin.types import GovernanceEvent, Seconds, Timestep, TimestepDict

SECONDS_PER_TIMESTEP: Seconds = 3600


GOVERNANCE_EVENTS = {0: GovernanceEvent('enable_control', {'enabled': True})}

raw_params: dict[str, Union[Param, ParamSweep]] = {
    'seconds_per_timestep': Param(SECONDS_PER_TIMESTEP, Seconds),
    'expected_blocktime': Param(15, Seconds),
    'governance_events': Param(None, dict[Timestep, GovernanceEvent]),
    'backtesting_data': Param(None, TimestepDict),
    'exogenous_data': Param(None, TimestepDict)
}

params = prepare_params(raw_params)
