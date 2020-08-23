BLOCKTIME = 15
P_constant = 0.01
I_constant = 0.001

# helpers
def calculate_p_rate(input, setpoint):
    return (setpoint - input) / input * P_constant

def calculate_i_rate(time_since_deviation):
    return time_since_deviation * I_constant

def calculate_target_rate(market_price, target_price, time_since_deviation):
    return calculate_p_rate(market_price, target_price)
    # return calculate_p_rate(market_price, target_price) + calculate_i_rate(time_since_deviation)

def did_deviation_update(target_price, market_price, latest_devation_type):
    deviation = target_price - market_price
    if (deviation >= 0 and latest_devation_type == -1):
        return False
    elif (deviation < 0 and latest_devation_type == 1):
        return False
    else:
        return True

# setters
def update_target_rate(_g, step, sL, s, input):
    target_rate = calculate_target_rate(s['market_price'], s['target_price'], s['time_since_deviation'])
    return ('target_rate', target_rate)

def update_target_price(_g, step, sL, s, input):
    target_price = s['target_price'] + (BLOCKTIME * s['target_rate'])
    if (target_price < 0):
        target_price = 0
    return ('target_price', target_price)

def update_market_price(_g, step, sL, s, input):
    add_to_market_price = 0
    if (s['timestep'] < 5):
        add_to_market_price = 0
    elif (s['timestep'] >= 5 and s['timestep'] < 10):
        add_to_market_price = 0.1
    else:
        delta = s['target_price'] - s['market_price']
        add_to_market_price = delta * 0.8
    return ('market_price', s['market_price'] + add_to_market_price)

def update_timestep(_g, step, sL, s, input):
    return ('timestep', s['timestep'] + 1)

def update_latest_deviation_type(_g, step, sL, s, input):
    deviation_type = 0
    deviation = s['target_price'] - s['market_price']
    if (deviation > 0):
        deviation_type = 1
    elif (deviation < 0):
        deviation_type = -1
    return ('latest_deviation_type', deviation_type)

def update_time_since_deviation(_g, step, sL, s, input):
    result = 0
    if (not did_deviation_update(s['target_price'], s['market_price'], s['latest_deviation_type'])):
        result = s['time_since_deviation'] + BLOCKTIME
    return ('time_since_deviation', result)
