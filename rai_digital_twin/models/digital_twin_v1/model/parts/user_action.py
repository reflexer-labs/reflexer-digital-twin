from rai_digital_twin.types import Parameters, State, UserAction


def extrapolate_user_action(params: Parameters,
                         state: State) -> UserAction:
    """
    Extrapolate User Action from the 
    Data-Driven Linearized Aggregated Arbitrageur Model
    https://hackmd.io/w-vfdZIMTDKwdEupeS3qxQ
    """
    pass


def p_user_action(params, _1, _2, state):
    """

    """

    mode = params['user_action_mode']

    user_action = {}
    if mode == 'backtesting':
        t = state['timestep']
        user_action = params['user_action_history'][t]
    elif mode == 'projection':
        user_action = extrapolate_user_action(params, state)
    else:
        pass

    return user_action
