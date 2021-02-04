import scipy.stats as sts
import numpy as np
import copy
import models.system_model_v3.model.parts.uniswap as uniswap
from .utils import print_time

def p_liquidity_demand(params, substep, state_history, state):
    RAI_delta = 0 # TODO: stochastic process for liquidity demand

    RAI_balance = state['RAI_balance']
    ETH_balance = state['ETH_balance']
    uniswap_fee = params['uniswap_fee']

    if RAI_delta >= 0:
        # TODO: confirm positive/negative dataset
        # Selling RAI
        _, ETH_delta = uniswap.get_input_price(RAI_delta, RAI_balance, ETH_balance, uniswap_fee)
    else:
        # Buying RAI
        ETH_delta, _ = uniswap.get_output_price(RAI_delta, RAI_balance, ETH_balance, uniswap_fee)
    
    return {'RAI_delta': RAI_delta, 'ETH_delta': ETH_delta, 'UNI_delta': 0}

@print_time
def p_market_price(params, substep, state_history, state):
    market_price = (state['ETH_balance'] / state['RAI_balance']) * state['eth_price']

    uniswap_oracle = params['uniswap_oracle']
    uniswap_oracle.update_result(state)
    median_price = uniswap_oracle.median_price

    return {"market_price": market_price, "market_price_twap": median_price}

def s_market_price(params, substep, state_history, state, policy_input):
    return "market_price", policy_input["market_price"]

def s_market_price_twap(params, substep, state_history, state, policy_input):
    return "market_price_twap", policy_input["market_price_twap"]
