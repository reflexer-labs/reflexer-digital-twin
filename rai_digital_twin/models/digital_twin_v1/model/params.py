from typing import Union
from cadCAD_tools.types import Param, ParamSweep
from cadCAD_tools.preparation import prepare_params
from rai_digital_twin.types import GovernanceEvent, Height, Seconds, Timestep, TimestepDict

raw_params: dict[str, Union[Param, ParamSweep]] = {
    'expected_blocktime': Param(15, Seconds),
    'heights': Param(None, dict[Timestep, Height]),
    'governance_events': Param({}, dict[Timestep, GovernanceEvent]),
    'backtesting_data': Param({}, TimestepDict),
    'exogenous_data': Param({}, TimestepDict)
}

params = prepare_params(raw_params)
