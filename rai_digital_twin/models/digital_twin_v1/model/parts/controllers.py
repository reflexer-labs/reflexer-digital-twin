from rai_digital_twin.types import ControllerParams, ControllerState
from rai_digital_twin.types import Percentage, Seconds
from math import exp


def redemption_rate(pid_params: ControllerParams,
                    pid_state: ControllerState,
                    cumulative_time: Seconds) -> Percentage:
    """
    Compute new redemption rate given the current controller params and state
    """
    # Compute new redemption rate
    if pid_params.enabled:
        # Update the Redemption Rate if the current cumulative time
        # is on par with the control period.
        control_parity = (cumulative_time % pid_params.period)
        update_redemption_rate = (control_parity == 0)
        if update_redemption_rate is True:
            proportional_rate = pid_params.kp * pid_state.proportional_error
            integral_rate = pid_params.ki * pid_state.integral_error
            integral_rate /= pid_params.period
            new_redemption_rate = proportional_rate + integral_rate
        else:
            new_redemption_rate = pid_state.redemption_rate
    else:
        new_redemption_rate = 0.0
    return new_redemption_rate


def p_observe_errors(_1, _2, _3, state):
    """
    Calculate the error between the redemption and market price.
    """
    error = (state["pid_state"].redemption_price - state["market_price_twap"])
    return {"error_star": error}


def s_pid_error(_1, _2, _3, state, signal):
    """
    Update and store the error integral state.
    Calculate the error integral using numerical integration (trapezoid rule).
    """
    # Parameters, state variables & policy inputs
    pid_params: ControllerParams = state['pid_params']
    pid_state: ControllerState = state['pid_state']
    timedelta = state["timedelta"]
    new_error = signal["error_star"]

    previous_integral = pid_state.integral_error
    old_error = pid_state.proportional_error

    # Numerical integration (trapezoid rule)
    mean_error = (old_error + new_error) / 2
    area = mean_error * timedelta

    # Perform leaky integration (alpha=1 means no leaky)
    scaled_alpha = pid_params.leaky_factor ** timedelta
    effective_previous_integral = scaled_alpha * previous_integral
    error_integral = effective_previous_integral + area

    new_pid_state = ControllerState(pid_state.redemption_price,
                                    pid_state.redemption_rate,
                                    new_error,
                                    error_integral)

    return ('pid_state', new_pid_state)


def s_pid_redemption(_1, _2, _3, state, _5):
    """
    Update the controller redemption price according to the redemption rate"
    """
    # State variables
    pid_state: ControllerState = state['pid_state']
    pid_params: ControllerParams = state['pid_params']
    timedelta = state['timedelta']
    cumulative_time = state['cumulative_time']

    # Compute new redemption price
    interest = exp(pid_state.redemption_rate * timedelta)
    new_redemption_price = pid_state.redemption_price * interest

    # Compute new redemption rate
    new_redemption_rate = redemption_rate(pid_params,
                                          pid_state,
                                          cumulative_time)

    # Return output
    new_pid_state = ControllerState(new_redemption_price,
                                    new_redemption_rate,
                                    pid_state.proportional_error,
                                    pid_state.integral_error)
    return ('pid_state', new_pid_state)
