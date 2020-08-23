# Helpers
def did_deviation_update(error, latest_devation_type):
    if (error >= 0 and latest_devation_type == -1):
        return False
    elif (error < 0 and latest_devation_type == 1):
        return False
    else:
        return True

# State update functions
def update_target_rate(params, substep, state_history, previous_state, policy_input):
    error = previous_state['target_price'] - previous_state['market_price']
    target_rate = params['kp'] * error + params['ki'] * previous_state['time_since_deviation']
    return ('target_rate', target_rate)

def update_target_price(params, substep, state_history, previous_state, policy_input):
    target_price = previous_state['target_price'] + (params['blocktime'] * previous_state['target_rate'])
    if (target_price < 0):
        target_price = 0
    return ('target_price', target_price)

def update_market_price(params, substep, state_history, previous_state, policy_input):
    add_to_market_price = 0
    if (previous_state['timestep'] < 5):
        add_to_market_price = 0
    elif (previous_state['timestep'] >= 5 and previous_state['timestep'] < 10):
        add_to_market_price = 0.1
    else:
        delta = previous_state['target_price'] - previous_state['market_price']
        add_to_market_price = delta * 0.8
    return ('market_price', previous_state['market_price'] + add_to_market_price)

def update_timestep(params, substep, state_history, previous_state, policy_input):
    return ('timestep', previous_state['timestep'] + 1)

def update_latest_deviation_type(params, substep, state_history, previous_state, policy_input):
    deviation_type = 0
    deviation = previous_state['target_price'] - previous_state['market_price']
    if (deviation > 0):
        deviation_type = 1
    elif (deviation < 0):
        deviation_type = -1
    return ('latest_deviation_type', deviation_type)

def update_time_since_deviation(params, substep, state_history, previous_state, policy_input):
    result = 0
    error = previous_state['target_price'] - previous_state['market_price']
    if (not did_deviation_update(error, previous_state['latest_deviation_type'])):
        result = previous_state['time_since_deviation'] + params['blocktime']
    return ('time_since_deviation', result)
