from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from autosklearn.regression import AutoSklearnRegressor
from autosklearn.metrics import mean_squared_error as auto_mean_squared_error
import matplotlib.pyplot as plt
import math, statistics
from functools import partial
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLSResults
from statsmodels.tsa.ar_model import AutoReg
from scipy.optimize import root, show_options, newton, minimize
import numpy as np
import seaborn as sns
import pickle
import time
import logging
import pandas as pd

from .debt_market import resolve_cdp_positions


# TODO: remove expected_debt_price 
# def p_resolve_expected_debt_price(params, substep, state_history, state):
#     model = params['model']
#     features = params['features']
#     feature_0 = get_feature(state_history, features, index=(0 if params['freeze_feature_vector'] else -1))
#     expected_debt_price = model.predict(feature_0)[0]
    
#     logging.debug(f'expected_debt_price: {expected_debt_price}')

#     return {'expected_debt_price': expected_debt_price}

# def s_store_expected_debt_price(params, substep, state_history, state, policy_input):
#     return 'expected_debt_price', policy_input['expected_debt_price']

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

# TODO: remove
# def p_apt_model(params, substep, state_history, state):
#     return {**cdp_position_state, 'feature_vector': feature_0, 'optimal_values': optimal_values, 'minimize_results': minimize_results}

def p_arbitrageur_model(params, substep, state_history, state):
    # TODO: possible metric - arb. profits/performance
    
    # TODO: calculate v, u for each CDP
    
    # Pass optimal values to CDP handler, and receive new initial condition from CDP handler
    # TODO: locks and draws, frees and wipes - independent
    # TODO: v, u will be deltas of CDP positions rather than aggregate, refactor
    cdp_position_state = resolve_cdp_positions(params, state, {'v_1': v_1, 'v_2 + v_3': v_2_v_3, 'u_1': u_1, 'u_2': u_2})
    # TODO: state update Q, D, cdp positions, actions passed to secondary market
    # locks and draws - sell
    # frees and wipes - buy
    
    return {**cdp_position_state}

# TODO: remove
# def s_store_feature_vector(params, substep, state_history, state, policy_input):
#     return 'feature_vector', policy_input['feature_vector']

# def s_store_optimal_values(params, substep, state_history, state, policy_input):
#     return 'optimal_values', policy_input['optimal_values']

# def s_store_minimize_results(params, substep, state_history, state, policy_input):
#     return 'minimize_results', policy_input['minimize_results']
