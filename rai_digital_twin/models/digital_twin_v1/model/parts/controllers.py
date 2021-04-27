import rai_digital_twin.models.options as options
import rai_digital_twin.models.constants as constants
import rai_digital_twin.failure_modes as failure


def update_redemption_rate(params, _1, _2, state, _4):
    """
    Calculate the PI controller redemption rate using the Kp and Ki constants
    and the error states.
    """
    if params['controller_enabled'] is True:
        # Only update the Redemption Rate if the current cumulative time
        # is on par with the control period
        control_parity = (state['cumulative_time'] % params['control_period'])
        update_redemption_rate = (control_parity == 0)
        if update_redemption_rate is True:
            error = state["error_star"]
            error_integral = state["error_star_integral"]
            kp_correction = params["kp"] * error
            ki_correction = params['ki'] * error_integral
            ki_correction /= params['control_period']
            redemption_rate = kp_correction + ki_correction
        else:
            redemption_rate = state['redemption_rate']
    else:
        redemption_rate = 0.0

    return ("redemption_rate", redemption_rate)


def update_redemption_price(_0, _1, _2, state, _4):
    """
    Update the controller redemption_price state ("redemption price") according
    to the controller redemption_rate state ("redemption rate")

    Notes:
    * exp(bt) = (1+b)**t for low values of b; but to avoid compounding errors
    * we should probably stick to the same implementation as the solidity version
    * redemption_price =  state['redemption_price'] * FXnum(state['redemption_rate'] * state['timedelta']).exp()
    * redemption_price =  state['redemption_price'] * math.exp(state['redemption_rate'] * state['timedelta'])
    """

    redemption_price = state["redemption_price"]

    try:
        interest = (1 + state['redemption_rate']) ** state["timedelta"]
        redemption_price *= interest
    except OverflowError as e:
        raise failure.ControllerTargetOverflowException(
            (e, redemption_price))

    if redemption_price < 0:
        redemption_price = 0
    else:
        pass

    return ("redemption_price", redemption_price)


def observe_errors(params, _1, _2, state):
    """
    Calculate the error between the redemption and market price, 
    using the error_term parameter.

    The error_term parameter allows you to set whether the error is calculated
    as redemption - market or market - redemption.
    """
    redemption_price = state["redemption_price"]

    if params["rescale_redemption_price"] is True:
        redemption_price *= params["liquidation_ratio"]
    else:
        pass

    error_function = params["error_term"]
    error = error_function(redemption_price, state["market_price_twap"])

    return {"error_star": error}


def store_error_star(_0, _1, _2, policy_input):
    """
    Store the error_star state, 
    which is the error between the redemption and market price.
    """
    error = policy_input["error_star"]
    return "error_star", error


def update_error_star_integral(params, _1, _2, state, policy_input):
    """
    Update and store the error integral state.

    Calculate the error integral using numerical integration (trapezoid rule).
    """
    # Numerical integration (trapezoid rule)
    error_star_integral = state["error_star_integral"]
    old_error = state["error_star"]  # unit: USD
    new_error = policy_input["error_star"]  # unit: USD
    mean_error = (old_error + new_error) / 2  # unit: USD
    timedelta = state["timedelta"]  # unit: time (seconds)
    area = mean_error * timedelta  # unit: USD * seconds

    # Select whether to implement a leaky integral or not
    if params[options.IntegralType.__name__] == options.IntegralType.LEAKY.value:
        alpha = params["alpha"]
        remaing_frac = float(alpha / constants.RAY) ** timedelta  # unitless
        # unit: USD * seconds
        remaining = int(remaing_frac * error_star_integral)
        error_integral = remaining + area  # unit: USD * seconds
    else:
        error_integral = error_star_integral + area  # unit: USD * seconds

    return ("error_star_integral", error_integral)
