#from models.v1.config import exp
from .helpers import *
from FixedPoint import FXnum

import options as options
import constants

### Stability Controller blocks


def update_target_rate(params, substep, state_history, state, policy_input):

    error = -state['error_star']
    error_integral = -state['error_star_integral']
    
    target_rate = params['kp'] * error + params['ki'] * error_integral
    
    key = 'target_rate'
    value = target_rate

    return key, value

def update_target_price(params, substep, state_history, state, policy_input):
    # target_price = state['target_price'] + (state['timedelta'] * state['target_rate'])
    # TODO: this is causing a bottleneck, see `python3 -m cProfile -s time models/v1/run.py`
    target_price =  state['target_price'] *FXnum(state['target_rate']*state['timedelta']).exp()
    
    if (target_price < 0):
        target_price = 0

    key = 'target_price'
    value = target_price

    return key, value

### Error accounting

def observe_errors(params, substep, state_history, state):

    error_star= state['target_price']-state['market_price']
    error_hat= state['debt_price']-state['market_price']

    return {'error_star':error_star, 'error_hat':error_hat}

def store_error_star(params, substep, state_history, state, policy_input):
    error = policy_input['error_star']
    return 'error_star', error

def update_error_star_integral(params, substep, state_history, state, policy_input):
    
    error_star_integral = state['error_star_integral']
    old_error = state['error_star']
    new_error = policy_input['error_star']
    mean_error = int((old_error + new_error)/2)
    timedelta = state['timedelta']
    area = mean_error * timedelta

    error_integral = None
    if params[options.IntegralType.__name__] == options.IntegralType.LEAKY.value:
        alpha = params['alpha']
        remaing_frac = float(alpha / constants.RAY)**timedelta
        remaining = int(remaing_frac * error_star_integral)
        error_integral = remaining + area
    else:
        error_integral = error_star_integral + area

    return 'error_star_integral', error_integral

def update_error_star_derivative(params, substep, state_history, state, policy_input):
    
    old_error = state['error_star']
    new_error = policy_input['error_star']

    theta = params['derivative_smoothing']

    error_derivative = theta*(new_error-old_error)/state['timedelta'] + (1-theta)*state['error_star_derivative']

    return 'error_star_derivative', error_derivative

def store_error_hat(params, substep, state_history, state, policy_input):
    error = policy_input['error_hat']
    return 'error_hat', error

def update_error_hat_integral(params, substep, state_history, state, policy_input):
    
    old_error = state['error_hat']
    new_error = policy_input['error_hat']

    mean_error = (old_error+new_error)/2

    area = mean_error*state['timedelta']
    
    error_integral = state['error_hat_integral'] + area

    return 'error_hat_integral', error_integral


def update_error_hat_derivative(params, substep, state_history, state, policy_input):
    old_error = state['error_star']
    new_error = policy_input['error_star']

    theta = params['derivative_smoothing']

    error_derivative = theta*(new_error-old_error)/state['timedelta']+(1-theta)*state['error_hat_derivative']

    return 'error_hat_derivative', error_derivative
