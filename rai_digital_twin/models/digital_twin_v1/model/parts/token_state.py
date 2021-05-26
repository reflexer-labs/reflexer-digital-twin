

from rai_digital_twin.system_identification import fit_predict_action
from rai_digital_twin.types import ActionState, TokenState
from cadCAD_tools.types import History, Params, Signal, State, VariableUpdate
from random import random

def state_to_action_state(state: State) -> ActionState:
    return ActionState(state['token_state'],
                       state['pid_state'],
                       state['market_price'],
                       state['eth_price']
                       )


def prepare_action_state_history(params: Params,
                                 history: History,
                                 state: State) -> list[ActionState]:

    # Backtesting action states
    states_1 = params['backtesting_action_states'].copy()

    # History action states
    states_2 = [state_to_action_state(substep_states[-1])
                for substep_states in history]

    # Last action state
    states_3 = [state_to_action_state(state)]

    return states_1 + states_2 + states_3


def p_user_action(params, _1, history, state) -> Signal:
    # Only run if the model is running on extrapolation mode
    if params['perform_backtesting'] is False:
        # Retrieve data on the last substep and on each point of history,
        # except for the last one.

        states = prepare_action_state_history(params,
                                              history,
                                              state)
        new_action = fit_predict_action(states,
                                        params['user_action_params'])

        new_state = state['token_state'] + new_action * (random() - 0.5) * 0.001 # HACK
        return {'token_state': new_state}
    else:
        return {}


def p_backtesting(params, _2, _3, state) -> Signal:
    if params['perform_backtesting'] is True:
        t = state['timestep']
        backtesting_data = params.get('backtesting_data', None)
        current_data = backtesting_data.get(t, state['token_state'])
        return {'token_state': current_data}
    else:
        return {}


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
