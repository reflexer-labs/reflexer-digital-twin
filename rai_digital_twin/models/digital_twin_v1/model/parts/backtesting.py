

from rai_digital_twin.types import TokenState
from cadCAD_tools.types import VariableUpdate


def p_backtesting(params, _2, _3, state):
    t = state['timestep']
    backtesting_data = params['backtesting_data']
    current_data = backtesting_data[t]
    return current_data


def s_token_state(_1, _2, _3, state, signal) -> VariableUpdate:
    token_state: TokenState = state['token_state']
    
    new_state = TokenState(signal.get('rai_reserve', token_state.rai_reserve),
                           signal.get('eth_reserve', token_state.eth_reserve),
                           signal.get('rai_debt', token_state.rai_debt),
                           signal.get('eth_locked', token_state.eth_locked),)

    state_override = signal.get('token_state', None)
    if state_override is not None:
        new_state = state_override
    else:
        pass

    return ('token_state', new_state)
