

from rai_digital_twin.system_identification import fit_predict_action
from rai_digital_twin.types import TokenState
from cadCAD_tools.types import Params, Signal, State, VariableUpdate


def p_user_action(params, _1, history, state) -> Signal:
    # Only run if the model is running on extrapolation mode
    if params['backtesting_data'] is None:
        # Retrieve data on the last substep and on each point of history,
        # except for the last one.
        past_states = [timestep_state[-1]
                    for timestep_state in history[:-1]]

        new_action = fit_predict_action(state,
                                        past_states,
                                        params['user_action_params'])

        return {'token_state': new_action}
    else:
        return {}


def p_backtesting(params, _2, _3, state) -> Signal:
    t = state['timestep']
    backtesting_data = params['backtesting_data']
    current_data = backtesting_data.get(t, state['token_state'])
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
