import scipy.stats as sts
import numpy as np


# TODO: stochastic process liquidity demand

def p_market_price(params, substep, state_history, state):
    market_price = (state['ETH_balance'] / state['RAI_balance']) * state['eth_price']

    uniswap_oracle = state['uniswap_oracle']
    uniswap_oracle.update_result(state)
    median_price = uniswap_oracle.median_price

    return {"market_price": market_price, "market_price_twap": median_price, "uniswap_oracle": uniswap_oracle}

def s_uniswap_oracle(params, substep, state_history, state, policy_input):
    return "uniswap_oracle", policy_input["uniswap_oracle"]

def s_market_price(params, substep, state_history, state, policy_input):
    return "market_price", policy_input["market_price"]

def s_market_price_twap(params, substep, state_history, state, policy_input):
    return "market_price_twap", policy_input["market_price_twap"]
