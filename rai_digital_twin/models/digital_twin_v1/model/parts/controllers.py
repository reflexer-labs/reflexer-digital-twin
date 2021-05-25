from rai_digital_twin.types import ControllerParams, ControllerState
from rai_digital_twin.types import Percentage, Seconds
from math import exp


def redemption_rate(pid_params: ControllerParams,
                    pid_state: ControllerState,
                    bound_params: dict) -> Percentage:
    """
    Compute new redemption rate given the current controller params and state
    """
    # Compute PI Output
    if pid_params.enabled:
        proportional_rate = pid_params.kp * pid_state.proportional_error
        integral_rate = pid_params.ki * pid_state.integral_error
        integral_rate /= pid_params.period
        pi_output = proportional_rate + integral_rate
    else:
        pi_output = 0.0

    # Redemption price & controller PI boundaries
    LOWER_BOUND = bound_params['lower_bound']
    UPPER_BOUND = bound_params['upper_bound']
    DEFAULT_REDEMPTION_RATE = bound_params['default_redemption_rate']
    NEGATIVE_RATE_LIMIT = bound_params['negative_rate_limit']

    if pi_output < LOWER_BOUND:
        adj_pi_output = LOWER_BOUND
    elif pi_output > UPPER_BOUND:
        adj_pi_output = UPPER_BOUND
    else:
        adj_pi_output = pi_output

    if adj_pi_output < 0:
        if -1 * adj_pi_output >= DEFAULT_REDEMPTION_RATE:
            new_redemption_rate = NEGATIVE_RATE_LIMIT
        elif adj_pi_output <= -1 * NEGATIVE_RATE_LIMIT:
            new_redemption_rate = DEFAULT_REDEMPTION_RATE - NEGATIVE_RATE_LIMIT
        else:
            new_redemption_rate = DEFAULT_REDEMPTION_RATE + adj_pi_output
    else:
        new_redemption_rate = DEFAULT_REDEMPTION_RATE + adj_pi_output

    return new_redemption_rate


def p_observe_errors(_1, _2, _3, state):
    """
    Calculate the error between the redemption and market price.
    """
    error = (state["pid_state"].redemption_price - state["market_price"])
    return {"error_star": error}


def s_pid_error(_1, _2, _3, state, signal):
    """
    Update and store the error integral state.
    Calculate the error integral using numerical integration (trapezoid rule).
    """
    # Parameters, state variables & policy inputs
    pid_params: ControllerParams = state['pid_params']
    pid_state: ControllerState = state['pid_state']
    timedelta = state["timedelta_in_hours"]
    new_error = signal["error_star"]

    if timedelta is not None:
        previous_integral = pid_state.integral_error
        old_error = pid_state.proportional_error

        # Numerical integration (trapezoid rule)
        mean_error = (old_error + new_error) / 2
        area = mean_error * timedelta

        # Perform leaky integration (alpha=1 means no leaky)
        if pid_params.ki > 0:
            scaled_alpha = pid_params.leaky_factor ** timedelta
            effective_previous_integral = scaled_alpha * previous_integral
            error_integral = effective_previous_integral + area
        else:
            error_integral = 0.0

        new_pid_state = ControllerState(pid_state.redemption_price,
                                        pid_state.redemption_rate,
                                        new_error,
                                        error_integral)
    else:
        new_pid_state = pid_state

    return ('pid_state', new_pid_state)


def s_pid_redemption(params, _2, _3, state, _5):
    """
    Update the controller redemption price according to the redemption rate"
    """
    # State variables
    pid_state: ControllerState = state['pid_state']
    pid_params: ControllerParams = state['pid_params']
    timedelta = state['timedelta_in_hours']

    # Compute new redemption price

    if timedelta is not None and state['timestep'] > 1:
        interest = pid_state.redemption_rate ** timedelta
        new_redemption_price = pid_state.redemption_price * interest

        # Compute new redemption rate
        new_redemption_rate = redemption_rate(pid_params,
                                              pid_state,
                                              params['pi_bound_params'])

        timedelta_in_seconds = timedelta * 60 * 60
        # Return output
        new_pid_state = ControllerState(new_redemption_price,
                                        new_redemption_rate ** timedelta_in_seconds,
                                        pid_state.proportional_error,
                                        pid_state.integral_error)
    else:
        new_pid_state = pid_state
    return ('pid_state', new_pid_state)
