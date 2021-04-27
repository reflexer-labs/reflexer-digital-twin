import rai_digital_twin.models.options as options
import rai_digital_twin.models.constants as constants
import rai_digital_twin.models.digital_twin_v1.model.parts.failure_modes as failure


def update_redemption_rate(params, substep, state_history, state, policy_input):
    """
    Calculate the PI controller redemption rate using the Kp and Ki constants and the error states.
    """

    if state['cumulative_time'] % params['control_period'] == 0:
        error = state["error_star"]  # unit USD
        error_integral = state["error_star_integral"]  # unit USD * seconds

        redemption_rate = (
            params["kp"] * error + (params["ki"] / params['control_period']) * error_integral
        )

        redemption_rate = redemption_rate if policy_input["controller_enabled"] else 0  # unitless
    else:
        redemption_rate = state['redemption_rate'] if policy_input["controller_enabled"] else 0

    return "redemption_rate", redemption_rate


def update_redemption_price(params, substep, state_history, state, policy_input):
    """
    Update the controller redemption_price state ("redemption price") according to the controller redemption_rate state ("redemption rate")

    Notes:
    * exp(bt) = (1+b)**t for low values of b; but to avoid compounding errors
    * we should probably stick to the same implementation as the solidity version
    * redemption_price =  state['redemption_price'] * FXnum(state['redemption_rate'] * state['timedelta']).exp()
    * redemption_price =  state['redemption_price'] * math.exp(state['redemption_rate'] * state['timedelta'])
    """

    redemption_price = state["redemption_price"]
    try:
        redemption_price = (
            state["redemption_price"] * (1 + state["redemption_rate"]) ** state["timedelta"]
        )
    except OverflowError as e:
        raise failure.ControllerredemptionOverflowException((e, redemption_price))

    if redemption_price < 0:
        redemption_price = 0

    return "redemption_price", redemption_price


def observe_errors(params, substep, state_history, state):
    """
    Calculate the error between the redemption and market price, using the error_term parameter.
    The error_term parameter allows you to set whether the error is calculated as redemption - market or market - redemption.
    """

    if params["rescale_redemption_price"] is True:
        redemption_price = state["redemption_price"] * params["liquidation_ratio"]
    else:
        redemption_price = state["redemption_price"]

    error_function = params["error_term"]
    error = error_function(redemption_price, state["market_price_twap"])

    return {"error_star": error}


def store_error_star(params, substep, state_history, state, policy_input):
    """
    Store the error_star state, which is the error between the redemption and market price.
    """

    error = policy_input["error_star"]

    return "error_star", error


def update_error_star_integral(params, substep, state_history, state, policy_input):
    """
    Update and store the error integral state.

    Calculate the error integral using numerical integration (trapezoid rule):
    See https://github.com/cadCAD-org/demos/blob/master/tutorials/numerical_computation/numerical_integration_1.ipynb
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
        remaining = int(remaing_frac * error_star_integral)  # unit: USD * seconds
        error_integral = remaining + area  # unit: USD * seconds
    else:
        error_integral = error_star_integral + area  # unit: USD * seconds

    return "error_star_integral", error_integral  # unit: USD * seconds
