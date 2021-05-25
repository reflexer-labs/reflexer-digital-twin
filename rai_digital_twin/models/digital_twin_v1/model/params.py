from typing import Union
from cadCAD_tools.types import Param, ParamSweep
from cadCAD_tools.preparation import prepare_params
from rai_digital_twin.types import GovernanceEvent, Height, Seconds, Timestep, TimestepDict, UserActionParams


USER_ACTION_PARAMS = UserActionParams(
    liquidation_ratio=1.5,
    debt_ceiling=1e8,
    uniswap_fee=0.003,
    consider_liquidation_ratio=True
)

raw_params: dict[str, Union[Param, ParamSweep]] = {
    'heights': Param(None, dict[Timestep, Height]),
    'governance_events': Param({}, dict[Timestep, GovernanceEvent]),
    'backtesting_data': Param({}, TimestepDict),
    'exogenous_data': Param({}, TimestepDict),
    'user_action_params': Param(USER_ACTION_PARAMS, UserActionParams),
    'block_time': Param(13.13, Seconds)
}

params = prepare_params(raw_params)
