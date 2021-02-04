def p_enable_controller(params, substep, state_history, state):
    controller_enabled = params['controller_enabled'] if state['cumulative_time'] >= params['enable_controller_time'] else False
    return {'controller_enabled': controller_enabled}
