import datetime as dt

def resolve_time_passed(params, substep, state_history, state):
    timestep_to_seconds_function = params['seconds_passed']
    seconds = timestep_to_seconds_function(state['timestep'])
    return {'seconds_passed': seconds}

def store_timedelta(params, substep, state_history, state, policy_input):
    value = policy_input['seconds_passed']
    key = 'timedelta'
    return (key, value)

def update_timestamp(params, substep, state_history, state, policy_input):
    seconds = policy_input['seconds_passed']
    value = state['timestamp'] + dt.timedelta(seconds = int(seconds))
    key = 'timestamp'
    return (key, value)

def update_blockheight(params, substep, state_history, state, policy_input):
    seconds = policy_input['seconds_passed']
    blocks = int(seconds / params['expected_blocktime'])
    value = state['blockheight'] + blocks
    key = 'blockheight'
    return (key, value)

def update_cumulative_time(params, substep, state_history, state, policy_input):
    seconds = policy_input['seconds_passed']
    value = state['cumulative_time'] + seconds
    return ('cumulative_time', value)
