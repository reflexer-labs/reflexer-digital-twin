

from rai_digital_twin.types import TokenState
from cadCAD_tools.types import Params, Signal, State, VariableUpdate


def extrapolate_user_action(params: Params,
                            state: State) -> TokenState:
    """
    Extrapolate User Action from
    https://hackmd.io/w-vfdZIMTDKwdEupeS3qxQ
    """
    pass


def p_user_action(params, _1, _2, state) -> Signal:
    """

    """
    return {}


def p_backtesting(params, _2, _3, state) -> Signal:
    t = state['timestep']
    backtesting_data = params['backtesting_data']
    current_data = backtesting_data[t]
    return {'token_state': current_data}


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
