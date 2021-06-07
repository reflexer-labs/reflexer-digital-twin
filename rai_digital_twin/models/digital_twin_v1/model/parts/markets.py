
def s_spot_price(_1, _2, _3, state, _5):
    token_state = state['token_state']
    eth_price = state['eth_price']
    spot_price = token_state.eth_reserve / token_state.rai_reserve
    spot_price *= eth_price
    return ('spot_price', spot_price)