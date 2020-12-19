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

from .utils import get_feature
from .debt_market import resolve_cdp_positions

def p_resolve_p_debt_expected(params, substep, state_history, state):
    model = params['model']
    features = params['features']
    feature_0 = get_feature(state_history, features, index=(0 if params['freeze_feature_vector'] else -1))
    p_debt_expected = model.predict(feature_0)[0]
    
    logging.debug(f'p_debt_expected: {p_debt_expected}')

    return {'p_debt_expected': p_debt_expected}

def s_store_p_debt_expected(params, substep, state_history, state, policy_input):
    return 'p_debt_expected', policy_input['p_debt_expected']

def p_resolve_p_expected(params, substep, state_history, state):
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
        
    # find root of non-arbitrage condition
    p_expected = (1 / alpha_1) * p * (interest_rate + beta_2 * (eth_price_mean - eth_price * interest_rate)
                                 + beta_1 * (market_price_mean - p * interest_rate)
                 ) - (alpha_0/alpha_1)
    
    logging.debug(f'p_expected terms: {alpha_1, p, interest_rate, beta_2, eth_price_mean, eth_price, beta_1, market_price_mean, alpha_0, p_expected}')

    return {'p_expected': p_expected}

def s_store_p_expected(params, substep, state_history, state, policy_input):
    return 'p_expected', policy_input['p_expected']

def p_apt_model(params, substep, state_history, state):
    start_time = time.time()

    logging.debug(f'''
    ##### APT model run #####
    Timestep: {state["timestep"]}
    ''')

    use_APT_ML_model = params['use_APT_ML_model']
    func = params['root_function']
    bounds = params['bounds']
    optvars = params['optvars']
    features = params['features']

    p_expected = state['p_expected']
    
    if use_APT_ML_model:
        optindex = [features.index(i) for i in optvars]
        feature_0 = get_feature(state_history, features, index=(0 if params['freeze_feature_vector'] else -1))
    else:
        # add regression constant; this shifts index for optimal values
        optindex = [features.index(i) + 1 for i in optvars]
        # Set the index to zero to use the same feature vector for every step
        feature_0 = get_feature(state_history, features, index=(0 if params['freeze_feature_vector'] else -1))
        feature_0 = np.insert(feature_0, 0, 1, axis=1)

    if params['test']['enable']:
        logging.info('APT test enabled')
        optimal_values = params['test']['params']['optimal_values']
        optimal_values = {k: optimal_values[k](timestep=state['timestep']) for k in optimal_values}

        v_1 = optimal_values.get('v_1', 0)
        v_2_v_3 = optimal_values.get('v_2 + v_3', 0)
        u_1 = optimal_values.get('u_1', 0)
        u_2 = optimal_values.get('u_2', 0)
        
        cdp_position_state = resolve_cdp_positions(params, state, {'v_1': v_1, 'v_2 + v_3': v_2_v_3, 'u_1': u_1, 'u_2': u_2})
        
        return {**cdp_position_state, 'feature_vector': feature_0, 'optimal_values': optimal_values}
        
    x0 = feature_0[:,optindex][0]

    logging.debug(f'''
    feature_0: {feature_0}
    x0: {x0}
    optvars: {optvars}
    p_expected: {p_expected}
    ''')

    minimize_results = {}
    try:
        if use_APT_ML_model:
            minimize_results = minimize(func, x0, method='Powell', 
                args=(optindex, feature_0, p_expected, state['timestep']),
                bounds = bounds,
                options={
                    'disp': True,
                    'maxiter': 10,
                    'maxfev': 10
                }
            )

            logging.debug(f'''
            Success: {minimize_results['success']}
            Message: {minimize_results['message']}
            Function value: {minimize_results['fun']}
            ''')
            
            x_star = minimize_results['x']
        else:
            x_star = newton(func, x0, args=(optindex, feature_0, p_expected))
        # Feasibility check, non-negativity
        negindex = np.where(x_star < 0)[0]
        if len(negindex) > 0:
            logging.warning('Negative root found, resetting')
            x_star[negindex] = x0[negindex]
    except RuntimeError as e:
        # For OLS, usually indicates non-convergence after 50 iterations (default)
        # Indicates not feasible to update CDP for this price/feature combination
        # Default to historical values here
        logging.error('Error: {}, default to historical values...'.format(e))
        x_star = x0
    
    optimal_values = dict((var, x_star[i]) for i, var in enumerate(optvars))
    
    logging.debug(f'''
    x_star: {x_star}
    optimal_values: {optimal_values}
    ''')
    
    v_1 = optimal_values.get('v_1', 0)
    v_2_v_3 = optimal_values.get('v_2 + v_3', 0)
    u_1 = optimal_values.get('u_1', 0)
    u_2 = optimal_values.get('u_2', 0)

    # Pass optimal values to CDP handler, and receive new initial condition from CDP handler
    cdp_position_state = resolve_cdp_positions(params, state, {'v_1': v_1, 'v_2 + v_3': v_2_v_3, 'u_1': u_1, 'u_2': u_2})
    
    logging.debug("--- %s seconds ---" % (time.time() - start_time))
    
    return {**cdp_position_state, 'feature_vector': feature_0, 'optimal_values': optimal_values, 'minimize_results': minimize_results}

def s_store_feature_vector(params, substep, state_history, state, policy_input):
    return 'feature_vector', policy_input['feature_vector']

def s_store_optimal_values(params, substep, state_history, state, policy_input):
    return 'optimal_values', policy_input['optimal_values']

def s_store_minimize_results(params, substep, state_history, state, policy_input):
    return 'minimize_results', policy_input['minimize_results']
