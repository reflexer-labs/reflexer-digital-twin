from typing import Union
from cadCAD_tools.types import Param, ParamSweep
from cadCAD_tools.preparation import prepare_params
from rai_digital_twin.types import ActionState, GovernanceEvent, Height, PIBoundParams, Seconds, Timestep, TimestepDict, UserActionParams


USER_ACTION_PARAMS = UserActionParams(
    liquidation_ratio=1.5,
    debt_ceiling=1e9,
    uniswap_fee=0.003,
    consider_liquidation_ratio=True,
    intensity=0.01
)

PI_BOUND_PARAMS = PIBoundParams(
    lower_bound=-1e-4,
    upper_bound=1e-4,
    default_redemption_rate=1.0,
    negative_rate_limit=0.1
)


raw_params: dict[str, Union[Param, ParamSweep]] = {
    # System wide parameters
    'governance_events': Param({}, dict[Timestep, GovernanceEvent]),
    'pi_bound_params': Param(PI_BOUND_PARAMS, PIBoundParams),
    'exogenous_data': Param({}, TimestepDict),
    
    # Backtesting specific parameters
    'heights': Param(None, dict[Timestep, Height]),
    'backtesting_data': Param({}, TimestepDict),
    'block_time': Param(13.13, Seconds),

    # Extrapolation specific parameters
    'backtesting_action_states': Param(None, tuple[ActionState]),
    'user_action_params': Param(USER_ACTION_PARAMS, UserActionParams),
    'extrapolation_timedelta': Param(60 * 60, Seconds),
    'ewm_alpha': Param(0.8, float),
    'var_lag': Param(15, int),

    # Misc
    'perform_backtesting': Param(True, bool)
}

params = prepare_params(raw_params)
