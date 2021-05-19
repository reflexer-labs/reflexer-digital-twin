from cadCAD_tools.types import Signal

def p_exogenous(params, _2, _3, state) -> Signal:
    exogenous_data = params['exogenous_data']
    if exogenous_data is not None:
        t = state['timestep']
        return exogenous_data[t]
    else:
        return {'eth_price': state['eth_price'],
                'market_price': state['market_price']}