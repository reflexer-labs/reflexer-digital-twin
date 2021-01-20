import math
import numpy as np
import time
import logging
import pandas as pd

from .debt_market import resolve_cdp_positions


def p_resolve_expected_market_price(params, substep, state_history, state):
    eth_return = state['eth_return']
    eth_price_mean = params['eth_price_mean']
    market_price_mean = params['market_price_mean']
    eth_returns_mean = params['eth_returns_mean']
    p = state['market_price']
    interest_rate = params['interest_rate']
    
    try:
        eth_price = state_history[-1][-1]['eth_price']
    except IndexError as e:
        logging.warning(e)
        eth_price = state['eth_price']

    alpha_0 = params['alpha_0']
    alpha_1 = params['alpha_1']
    beta_0 = params['beta_0']
    beta_1 = params['beta_1']
    beta_2 = params['beta_2']
        
    # TODO: derive betas, or proxy based on stoch. process
    # TODO: maybe assumption, same types of price movements as historical MakerDAO DAI
    expected_market_price = (1 / alpha_1) * p * (interest_rate + beta_2 * (eth_price_mean - eth_price * interest_rate)
                                 + beta_1 * (market_price_mean - p * interest_rate) # TODO: changed to reflect stoch. process
                 ) - (alpha_0/alpha_1)
    
    logging.debug(f'expected_market_price terms: {alpha_1, p, interest_rate, beta_2, eth_price_mean, eth_price, beta_1, market_price_mean, alpha_0, expected_market_price}')

    # TODO: E_t p(t+1) in hackmd
    return {'expected_market_price': expected_market_price}

def s_store_expected_market_price(params, substep, state_history, state, policy_input):
    return 'expected_market_price', policy_input['expected_market_price']

def p_arbitrageur_model(params, substep, state_history, state):
    # TODO: possible metric - arb. profits/performance
    
    # TODO: calculate v, u for each CDP
    
    # Pass optimal values to CDP handler, and receive new initial condition from CDP handler
    # TODO: locks and draws, frees and wipes - independent
    # TODO: v, u will be deltas of CDP positions rather than aggregate, refactor
    
    # cdp_position_state = resolve_cdp_positions(params, state, {'v_1': v_1, 'v_2 + v_3': v_2_v_3, 'u_1': u_1, 'u_2': u_2})

    cdp_position_state = {
        "cdps": state['cdps'],
        "u_1": state['u_1'],
        "u_2": state['u_2'],
        "v_1": state['v_1'],
        "v_2": state['v_2'],
        "v_2 + v_3": state['v_2'] + state['v_3'],
        "w_2": state['w_2'],
    }
    
    # TODO: state update Q, D, cdp positions, actions passed to secondary market
    # locks and draws - sell
    # frees and wipes - buy
    
    return {**cdp_position_state, 'optimal_values': {}}

# TODO: remove
# def s_store_feature_vector(params, substep, state_history, state, policy_input):
#     return 'feature_vector', policy_input['feature_vector']

def s_store_optimal_values(params, substep, state_history, state, policy_input):
    return 'optimal_values', policy_input['optimal_values']

# def s_store_minimize_results(params, substep, state_history, state, policy_input):
#     return 'minimize_results', policy_input['minimize_results']
