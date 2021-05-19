import datetime as dt

def p_resolve_time_passed(params, _2, _3, state):
    # Params & variables
    heights = params['heights']
    expected_blocktime = params['expected_blocktime']
    t = state['timestep']
    height = state['height']

    # Compute how much time it went
    if heights is not None:
        new_height = heights[t]
        if height is not None:
            height_difference = new_height - height
            seconds_passed = height_difference * expected_blocktime
        else:
            seconds_passed = None

        # Output
        return {'seconds_passed': seconds_passed,
                'height': new_height}
    else:
        return {'seconds_passed': 0.0,
                'height': state['height']}


def s_update_cumulative_time(_1, _2, _3, state, policy_input):
    seconds = policy_input['seconds_passed']
    value = state['cumulative_time']
    if value is None:
        value = seconds
    else:
        value += seconds
    return ('cumulative_time', value)
