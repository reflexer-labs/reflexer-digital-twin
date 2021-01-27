def p_enable_controller(params, substep, state_history, state):
    # TODO: enable/disable governance
    if state['cumulative_time'] >= 7 * 24 * 3600:
        params['controller_enabled'] = True
    else:
        params['controller_enabled'] = False

    return {'controller_enabled': params['controller_enabled']}
