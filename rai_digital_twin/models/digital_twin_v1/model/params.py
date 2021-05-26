from typing import Union
from cadCAD_tools.types import Param, ParamSweep
from cadCAD_tools.preparation import prepare_params
from rai_digital_twin.types import ActionState, GovernanceEvent, Height, PIBoundParams, Seconds, Timestep, TimestepDict, UserActionParams


USER_ACTION_PARAMS = UserActionParams(
    liquidation_ratio=1.5,
    debt_ceiling=1e8,
    uniswap_fee=0.003,
    consider_liquidation_ratio=True
)

PI_BOUND_PARAMS = PIBoundParams(
    lower_bound=-10.0,
    upper_bound=10.0,
    default_redemption_rate=1.0,
    negative_rate_limit=0.1
)


raw_params: dict[str, Union[Param, ParamSweep]] = {
    'heights': Param(None, dict[Timestep, Height]),
    'governance_events': Param({}, dict[Timestep, GovernanceEvent]),
    'backtesting_data': Param({}, TimestepDict),
    'backtesting_action_states': Param(None, tuple[ActionState]),
    'perform_backtesting': Param(False, bool),
    'exogenous_data': Param({}, TimestepDict),
    'user_action_params': Param(USER_ACTION_PARAMS, UserActionParams),
    'block_time': Param(13.13, Seconds),
    'pi_bound_params': Param(PI_BOUND_PARAMS, PIBoundParams)
}

params = prepare_params(raw_params)
