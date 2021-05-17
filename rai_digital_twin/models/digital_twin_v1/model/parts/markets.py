from rai_digital_twin.types import TokenState
import rai_digital_twin.failure_modes as failure


def s_token_state(_1, _2, _3, state, signal):
    new_token_state = TokenState(0.0, 0.0, 0.0, 0.0)
    return ('token_state', new_token_state)

