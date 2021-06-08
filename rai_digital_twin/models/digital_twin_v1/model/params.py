from typing import Union
from cadCAD_tools.types import Param, ParamSweep
from rai_digital_twin.types import ActionState, GovernanceEvent, Height, PIBoundParams, Percentage, Seconds, Timestep, TimestepDict, UserActionParams


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

NUMERICAL_PARAMS = {'ewm_alpha',
                    'var_lag',
                    'convergence_swap_intensity',
                    'extrapolation_timedelta',
                    'block_time'}


params: dict[str, Union[Param, ParamSweep]] = {
    # System wide parameters
    'governance_events': Param({}, dict[Timestep, GovernanceEvent]),
    'pi_bound_params': Param(PI_BOUND_PARAMS, PIBoundParams),
    'exogenous_data': Param(None, TimestepDict),

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
    'convergence_swap_intensity': Param([None], Percentage),

    # Misc
    'perform_backtesting': Param(True, bool)
}
