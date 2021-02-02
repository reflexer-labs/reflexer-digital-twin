def p_enable_controller(params, substep, state_history, state):
    # TODO: enable/disable governance
    controller_enabled = params['controller_enabled'] if state['cumulative_time'] >= 7 * 24 * 3600 else False
    return {'controller_enabled': controller_enabled}
