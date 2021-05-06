from rai_digital_twin.types import Parameters, State, UserAction


def extrapolate_user_action(params: Parameters,
                         state: State) -> UserAction:
    """
    Extrapolate User Action from
    https://hackmd.io/w-vfdZIMTDKwdEupeS3qxQ
    """
    pass


def p_user_action(params, _1, _2, state) -> UserAction:
    """

    """

    mode = params['user_action_mode']

    if mode == 'backtesting':
        t = state['timestep']
        user_action = params['user_action_history'][t]
    elif mode == 'projection':
        user_action = extrapolate_user_action(params, state)
    else:
        pass

    return user_action


def s_CDP_action(params, _1, _2, state, signal):
    return ('cdps', state['cdps'])
