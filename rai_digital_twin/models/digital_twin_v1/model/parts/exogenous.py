from rai_digital_twin.types import RAI_per_USD, TokenState
from cadCAD_tools.types import Signal, VariableUpdate

def p_exogenous(params, _2, _3, state) -> Signal:
    exogenous_data = params['exogenous_data']
    if exogenous_data is not None:
        t = state['timestep']
        return exogenous_data[t]
    else:
        return {'eth_price': state['eth_price'],
                'market_price': state['market_price']}

def s_market_price(params, _2, _3, state, signal) -> VariableUpdate:
    key = 'market_price'
    if key in signal:
        return (key, signal[key])
    else:
        token_state: TokenState = state['token_state']
        rai_per_eth: float = token_state.rai_reserve / token_state.eth_reserve
        value: RAI_per_USD = state['eth_price'] * rai_per_eth
        return (key, value)