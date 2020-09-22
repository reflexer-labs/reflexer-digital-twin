import scipy.stats as sts
import datetime as dt
from FixedPoint import FXnum

import options

def resolve_time_passed(params, substep, state_history, state):
    """
    Time passes 
    """
    
    if params[options.DebtPriceSource.__name__] == options.DebtPriceSource.EXTERNAL.value:
        seconds = max(params['minumum_control_period'], params['seconds_passed'](state['timestep']))
    else:
        offset = params['minumum_control_period']
        expected_lag = params['expected_control_delay']
        seconds = int(sts.expon.rvs(loc=offset, scale = expected_lag))

    return {'seconds_passed': seconds}


def store_timedelta(params, substep, state_history, state, policy_input):

    value = policy_input['seconds_passed']
    key = 'timedelta'

    return key,value

def update_timestamp(params, substep, state_history, state, policy_input):

    seconds = policy_input['seconds_passed']
    value = state['timestamp'] + dt.timedelta(seconds = int(seconds))
    key = 'timestamp'

    return key,value

def update_blockheight(params, substep, state_history, state, policy_input):

    seconds = policy_input['seconds_passed']
    blocks = int(seconds/params['expected_blocktime'])
    value = state['blockheight']+ blocks
    key = 'blockheight'

    return key,value

def resolve_debt_price(params, substep, state_history, state):
    """
    driving process
    """
    
    if params[options.DebtPriceSource.__name__] == options.DebtPriceSource.EXTERNAL.value:
        price_move = params['price_move'](state['timestep'])
    elif params[options.DebtPriceSource.__name__] == options.DebtPriceSource.DEBT_MARKET_MODEL.value:
        price_move = params['price_move'](state['timestep'])
    else:
        base_var = params['debt_market_std']
        variance = float(base_var*state['timedelta']/3600.0) #converting seconds to hours
        price_move = sts.norm.rvs(loc=0, scale=variance)

    return {'price_move':price_move}

def update_debt_price(params, substep, state_history, state, policy_input):

    price_move = policy_input['price_move']
    value = FXnum(state['debt_price'] + price_move)
    key = 'debt_price'

    return key,value

# 'p': 0.72309613,
# 'e_hat': 0.79603861,
# 'e_star': -0.72309613,
# 'cumsum_e_hat': 0.10020752,
# 'cumsum_e_star': 0.00376792,
# 'delta_e_hat': 0.10022812,
# 'delta_e_star': 0.09343981,
# 'intercept': 0.27520027628864485
    
# p = y_hat_prime[-1]
# e_hat = r['p_hat'] - p
# e_star = r['p_star'] - p
# cumsum_e_hat += e_hat
# cumsum_e_star += e_star
# delta_e_hat = e_hat - prev_e_hat
# delta_e_star = e_star - prev_e_star
# pred = (p * reg.coef_[0] +
#         e_hat * reg.coef_[1] + 
#         e_star * reg.coef_[2] +
#         cumsum_e_hat * reg.coef_[3] +
#         cumsum_e_star * reg.coef_[4] +
#         delta_e_hat * reg.coef_[5] +
#         delta_e_star * reg.coef_[6] +
#         reg.intercept_)

def update_market_price(params, substep, state_history, state, policy_input):

    hat_error = state['error_hat']
    hat_integral = state['error_hat_integral']
    hat_derivative = state['error_hat_derivative']
    hat_dp = params['kp-hat'] * hat_error + params['ki-hat'] * hat_integral + params['kd-hat'] * hat_derivative

    star_error = state['error_star']
    star_integral = state['error_star_integral']
    star_derivative = state['error_star_derivative']
    star_dp = params['kp-star'] * star_error + params['ki-star'] * star_integral + params['kd-star'] * star_derivative

    market_price = params['k0'] + params['k-autoreg-1']*state['market_price'] + star_dp + hat_dp

    if market_price < 0:
        value = 0
    else:
        value = market_price

    key = 'market_price'
  
    return key, value