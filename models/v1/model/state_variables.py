import datetime as dt
from FixedPoint import FXnum

state_variables = {
    'error_star': FXnum(0.0), #price units
    'error_hat': FXnum(0.0), #price units
    'old_error_star': FXnum(0.0), #price units
    'old_error_hat': FXnum(0.0), #price units
    'error_star_integral': FXnum(0.0), #price units x seconds
    'error_hat_integral': FXnum(0.0), #price units x seconds
    'error_star_derivative': FXnum(0.0), #price units per second
    'error_hat_derivative': FXnum(0.0), #price units per second
    'target_rate': FXnum(0.0), #price units per second
    'target_price': FXnum(1.0), #price units
    'market_price': FXnum(1.0), #price units
    'debt_price': FXnum(1.0), #price units
    'timedelta': int(0), #seconds
    'timestamp': dt.datetime.now(), #datetime
    'blockheight': int(0), #block offset (init 0 simplicity)
    # # Env. process states
    # 'seconds_passed': int(0), 
    # 'price_move': 1.0,
}
