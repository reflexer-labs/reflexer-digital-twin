from .helpers import *

def update_target_rate(params, substep, state_history, previous_state, policy_input):
    error = previous_state['error']
    error_integral = previous_state['error_integral']
    target_rate = params['kp'] * error + params['ki'] * error_integral
    return 'target_rate', target_rate

def update_target_price(params, substep, state_history, previous_state, policy_input):
    target_price = previous_state['target_price'] + (params['blocktime'] * previous_state['target_rate'])
    if (target_price < 0):
        target_price = 0
    return 'target_price', target_price

def update_market_price(params, substep, state_history, previous_state, policy_input):
    add_to_market_price = 0
    if (previous_state['timestep'] < 5):
        add_to_market_price = 0
    elif (previous_state['timestep'] >= 5 and previous_state['timestep'] < 10):
        add_to_market_price = 0.1
    else:
        error = previous_state['error']
        add_to_market_price = error * 0.8
    return 'market_price', previous_state['market_price'] + add_to_market_price

def update_error(params, substep, state_history, previous_state, policy_input):
    error = previous_state['target_price'] - previous_state['market_price']
    return 'error', error

def update_error_integral(params, substep, state_history, previous_state, policy_input):
    error_integral = previous_state['error_integral'] + previous_state['error']
    return 'error_integral', error_integral
