from rai_digital_twin.types import TokenState
import rai_digital_twin.failure_modes as failure


def s_token_state(_1, _2, _3, state, signal):
    new_token_state = TokenState(0.0, 0.0, 0.0, 0.0)
    return ('token_state', new_token_state)


def s_spot_price(_1, _2, _3, state, _5):
    token_state = state['token_state']
    eth_price = state['eth_price']
    spot_price = token_state.eth_reserve / token_state.rai_reserve
    spot_price *= eth_price
    return ('spot_price', spot_price)