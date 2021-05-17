import rai_digital_twin.models.constants as constants
import rai_digital_twin.failure_modes as failure
from math import exp

def s_redemption_rate(params, _1, _2, state, _4):
    """
    Calculate the PI controller redemption rate using the Kp and Ki constants
    and the error states.
    """
    # State and parameters
    controller_enabled = params['controller_enabled']
    control_period = params['control_period']
    ki = params['ki']
    kp = params['kp']
    error = state["error_star"]
    error_integral = state["error_star_integral"]
    cumulative_time = state['cumulative_time']
    previous_redemption_rate = state['redemption_rate']

    # Compute new redemption rate
    if controller_enabled == True:
        # Update the Redemption Rate if the current cumulative time
        # is on par with the control period.
        control_parity = (cumulative_time % control_period)
        update_redemption_rate = (control_parity == 0)
        if update_redemption_rate is True:
            proportional_correction = kp * error
            integral_correction = ki * error_integral / control_period
            new_redemption_rate = proportional_correction + integral_correction
        else:
            new_redemption_rate = previous_redemption_rate
    else:
        new_redemption_rate = 0.0

    # Output
    return ("redemption_rate", new_redemption_rate)


def s_redemption_price(_0, _1, _2, state, _4):
    """
    Update the controller redemption price according to the redemption rate"
    """
    # State variables
    redemption_price = state["redemption_price"]
    redemption_rate = state['redemption_rate']
    timedelta = state['timedelta']

    # Compute new redemption price
    interest = exp(redemption_rate * timedelta)
    new_redemption_price = redemption_price * interest

    # Return output
    return ("redemption_price", new_redemption_price)


def p_observe_errors(params, _1, _2, state):
    """
    Calculate the error between the redemption and market price.
    """
    error = (state["redemption_price"] - state["market_price_twap"])
    return {"error_star": error}


def s_error_star_integral(params, _1, _2, state, policy_input):
    """
    Update and store the error integral state.

    Calculate the error integral using numerical integration (trapezoid rule).
    """
    # Parameters, state variables & policy inputs
    alpha = params["alpha"]
    previous_integral = state["error_star_integral"]
    old_error = state["error_star"]
    timedelta = state["timedelta"]
    is_leaky = state['leaky_integral_activated']
    new_error = policy_input["error_star"]

    # Numerical integration (trapezoid rule)
    mean_error = (old_error + new_error) / 2 
    area = mean_error * timedelta

    # Select whether to implement a leaky integral or not
    if is_leaky:
        scaled_alpha = alpha ** timedelta 
        effective_previous_integral = scaled_alpha * previous_integral
        error_integral = effective_previous_integral + area 
    else:
        error_integral = previous_integral + area

    return ("error_star_integral", error_integral)
