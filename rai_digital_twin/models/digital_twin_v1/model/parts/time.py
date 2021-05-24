import datetime as dt

def p_resolve_time_passed(params, _2, _3, state):
    # Params & variables
    current_time = state['seconds_passed']
    t = state['timestep']
    heights = params.get('heights', None)
    if heights is None:
        return {'timedelta': state['pid_params'].period}
    else:
        delta = heights.get(t, current_time) - heights.get(t - 1, 0)
        return {'timedelta': delta}


def s_seconds_passed(_1, _2, _3, state, signal):
    return ('seconds_passed', state['seconds_passed'] + signal['timedelta'])

def s_timedelta_in_hours(_1, _2, _3, state, signal):
    return ('timedelta_in_hours', signal['timedelta'] / (60 * 60))