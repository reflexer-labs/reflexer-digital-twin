from rai_digital_twin.types import RAI_per_USD, TokenState
from cadCAD_tools.types import Signal, VariableUpdate


def p_exogenous(params, _2, _3, state) -> Signal:
    exogenous_data = params['exogenous_data']
    t = state['timestep']

    output = {}
    if t in exogenous_data:
        output.update(**exogenous_data[t])
    else:
        output.update(**{'eth_price': state['eth_price'],
                         'market_price': state['market_price']})
    return output


def s_market_price(params, _2, _3, state, signal) -> VariableUpdate:
    key = 'market_price'
    if key in signal:
        return (key, signal[key])
    else:
        token_state: TokenState = state['token_state']
        k = params['market_price_scale']  # HACK
        eth_per_rai: float = k * token_state.eth_reserve / token_state.rai_reserve
        value: RAI_per_USD = state['eth_price'] * eth_per_rai
        return (key, value)
