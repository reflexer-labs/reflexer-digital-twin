import datetime as dt
 

state_variables = {
    'error_star': (0.0), #price units
    'error_hat': (0.0), #price units
    'old_error_star': (0.0), #price units
    'old_error_hat': (0.0), #price units
    'error_star_integral': (0.0), #price units x seconds
    'error_hat_integral': (0.0), #price units x seconds
    'error_star_derivative': (0.0), #price units per second
    'error_hat_derivative': (0.0), #price units per second
    'target_rate': (0.0), #price units per second
    'target_price': (2.0), #price units
    'market_price': (2.0), #price units
    'debt_price': (2.0), #price units
    'timedelta': int(0), #seconds
    'timestamp': dt.datetime.strptime('12/18/18', '%m/%d/%y'), #datetime
    'blockheight': int(0), #block offset (init 0 simplicity)
    # # Env. process states
    # 'seconds_passed': int(0), 
    # 'price_move': 1.0,
}
