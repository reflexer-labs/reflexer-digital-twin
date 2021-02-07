import scipy.stats as sts
import numpy as np
import copy
import random
import logging

import models.system_model_v3.model.parts.uniswap as uniswap
from .utils import print_time

def p_liquidity_demand(params, substep, state_history, state):
    if params['liquidity_demand_enabled']:
        RAI_balance = state['RAI_balance']
        ETH_balance = state['ETH_balance']
        UNI_supply = state['UNI_supply']

        market_price = state['market_price']
        eth_price = state['eth_price']
        
        uniswap_fee = params['uniswap_fee']

        swap = random.randint(0, 1)
        # Positive == swap in, or add liquidity event; negative == swap out or remove liquidity event
        direction = 1 if random.randint(0, 1) else -1

        UNI_delta = 0
        if swap:
            # Draw from swap process
            RAI_delta = abs(params['token_swap_events'](state['run'], state['timestep']) * 1e-18)
            RAI_delta = min(RAI_delta, RAI_balance * params['liquidity_demand_shock_percentage']) \
                if params['liquidity_demand_shock'] \
                else min(RAI_delta, RAI_balance * params['liquidity_demand_max_percentage'])
            RAI_delta = RAI_delta * direction

            if RAI_delta >= 0:
                # Selling RAI
                _, ETH_delta = uniswap.get_input_price(RAI_delta, RAI_balance, ETH_balance, uniswap_fee)
                assert ETH_delta <= 0, (ETH_delta, RAI_delta)
                assert ETH_delta <= ETH_balance, (ETH_delta, ETH_balance)
            else:
                # Buying RAI
                ETH_delta, _ = uniswap.get_output_price(abs(RAI_delta), ETH_balance, RAI_balance, uniswap_fee)
                assert ETH_delta > 0, (ETH_delta, RAI_delta)
                assert RAI_delta <= RAI_balance, (RAI_delta, RAI_balance)
        else:
            # Draw from liquidity process
            RAI_delta = abs(params['liquidity_demand_events'](state['run'], state['timestep']) * 1e-18)
            RAI_delta = min(RAI_delta, RAI_balance * params['liquidity_demand_shock_percentage']) \
                if params['liquidity_demand_shock'] \
                else min(RAI_delta, RAI_balance * params['liquidity_demand_max_percentage'])
            RAI_delta = RAI_delta * direction

            if RAI_delta >= 0:
                ETH_delta, RAI_delta, UNI_delta = uniswap.add_liquidity(ETH_balance, RAI_balance, UNI_supply, RAI_delta, RAI_delta * market_price / eth_price)
                assert ETH_delta >= 0
                assert RAI_delta >= 0
                assert UNI_delta >= 0
            else:
                ETH_delta, RAI_delta, UNI_delta = uniswap.remove_liquidity(ETH_balance, RAI_balance, UNI_supply, abs(RAI_delta))
                assert ETH_delta <= 0
                assert ETH_delta <= ETH_balance, (ETH_delta, ETH_balance)
                assert RAI_delta <= 0
                assert UNI_delta <= 0

        logging.debug(f"Secondary market {'swap' if swap else 'liquidity demand'}: {RAI_delta=} {ETH_delta=} {UNI_delta=}")
        return {'RAI_delta': RAI_delta, 'ETH_delta': ETH_delta, 'UNI_delta': UNI_delta}
    else:
        return {'RAI_delta': 0, 'ETH_delta': 0, 'UNI_delta': 0}
    

def s_liquidity_demand(params, substep, state_history, state, policy_input):
    liquidity_demand = policy_input['RAI_delta']
    return 'liquidity_demand', liquidity_demand

def s_liquidity_demand_mean(params, substep, state_history, state, policy_input):
    liquidity_demand = policy_input['RAI_delta']
    liquidity_demand_mean = (state['liquidity_demand_mean'] + liquidity_demand) / 2
    return 'liquidity_demand_mean', liquidity_demand_mean

def p_market_price(params, substep, state_history, state):
    market_price = (state['ETH_balance'] / state['RAI_balance']) * state['eth_price']

    uniswap_oracle = copy.deepcopy(state['uniswap_oracle'])
    uniswap_oracle.update_result(state)
    median_price = uniswap_oracle.median_price

    return {"market_price": market_price, "market_price_twap": median_price, "uniswap_oracle": uniswap_oracle}

def s_market_price(params, substep, state_history, state, policy_input):
    return "market_price", policy_input["market_price"]

def s_market_price_twap(params, substep, state_history, state, policy_input):
    return "market_price_twap", policy_input["market_price_twap"]

def s_uniswap_oracle(params, substep, state_history, state, policy_input):
    return "uniswap_oracle", policy_input["uniswap_oracle"]
