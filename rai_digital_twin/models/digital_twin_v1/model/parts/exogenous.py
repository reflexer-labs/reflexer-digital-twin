from cadCAD_tools.types import Signal

def p_exogenous(params, _2, _3, state) -> Signal:
    exogenous_data = params['exogenous_variables']
    t = state['timestep']
    return exogenous_data[t]