import scipy.stats as sts
import numpy as np


def update_market_price(params, substep, state_history, state, policy_input):
    market_price = (state['ETH_balance'] / state['RAI_balance']) * state['eth_price']
    return "market_price", market_price
