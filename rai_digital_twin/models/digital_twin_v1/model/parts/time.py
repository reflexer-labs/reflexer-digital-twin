import datetime as dt

def p_resolve_time_passed(params, substep, state_history, state):
    timestep_to_seconds_function = params['seconds_passed']
    seconds = timestep_to_seconds_function(state['timestep'])
    return {'seconds_passed': seconds}


def s_store_timedelta(params, substep, state_history, state, policy_input):
    value = policy_input['seconds_passed']
    key = 'timedelta'
    return (key, value)


def s_update_cumulative_time(params, substep, state_history, state, policy_input):
    seconds = policy_input['seconds_passed']
    value = state['cumulative_time'] + seconds
    return ('cumulative_time', value)
