import options as options
import constants

### Stability Controller blocks

def update_target_rate(params, substep, state_history, state, policy_input):

    error = state['error_star'] # unit USD
    error_integral = state['error_star_integral'] # unit USD * seconds

    target_rate = params['kp'] * error + params['ki'](state['timedelta']) * error_integral
    
    key = 'target_rate'
    value = target_rate if params['controller_enabled'] else 0 # unitless

    return key, value

def update_target_price(params, substep, state_history, state, policy_input):
    # exp(bt) = (1+b)**t for low values of b; but to avoid compounding errors 
    # we should probably stick to the same implementation as the solidity version
    # target_price =  state['target_price'] * FXnum(state['target_rate'] * state['timedelta']).exp()
    # target_price =  state['target_price'] * math.exp(state['target_rate'] * state['timedelta'])
    
    target_price = state['target_price']
    try:
        target_price = state['target_price'] * (1 + state['target_rate'])**state['timedelta']
    except OverflowError:
        # print(f'Controller target price OverflowError: target price {target_price}; target rate {state["target_rate"]}')
        target_price = state['target_price']
        raise
    
    if (target_price < 0):
        target_price = 0
    # elif target_price > 10:
    #     print('Target price capped at 10')
    #     target_price = state['target_price']

    key = 'target_price'
    value = target_price

    return key, value

### Error accounting

def observe_errors(params, substep, state_history, state):

    error_star = params['error_term'](state['target_price'], state['market_price'])
    # error_hat = state['debt_price'] - state['market_price']

    return {'error_star': error_star} # , 'error_hat': error_hat

def store_error_star(params, substep, state_history, state, policy_input):
    error = policy_input['error_star']
    return 'error_star', error

def update_error_star_integral(params, substep, state_history, state, policy_input):
    
    error_star_integral = state['error_star_integral']
    old_error = state['error_star'] # unit: USD
    new_error = policy_input['error_star'] # unit: USD
    mean_error = (old_error + new_error)/2 # unit: USD
    timedelta = state['timedelta'] # unit: time (seconds)
    area = mean_error * timedelta # unit: USD * seconds

    if params[options.IntegralType.__name__] == options.IntegralType.LEAKY.value:
        alpha = params['alpha']
        remaing_frac = float(alpha / constants.RAY)**timedelta # unitless
        remaining = int(remaing_frac * error_star_integral) # unit: USD * seconds
        error_integral = remaining + area # unit: USD * seconds
    else:
        error_integral = error_star_integral + area # unit: USD * seconds

    return 'error_star_integral', error_integral # unit: USD * seconds
