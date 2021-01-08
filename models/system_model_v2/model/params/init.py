import numpy as np
import pandas as pd

import models.options as options
from models.constants import SPY, RAY

from models.system_model_v2.model.params.apt import *
from models.system_model_v2.model.state_variables.historical_state import \
    start_date, debt_market_df, eth_price_mean, eth_returns_mean, market_price_mean, stability_fee


# Set dataframe to start from start date
debt_market_df = debt_market_df.loc[start_date:]

# Assume
# TODO: update based on discussion with Stefan
halflife = SPY / 52 # weeklong halflife
alpha = int(np.power(.5, float(1 / halflife)) * RAY)

# Save partial simulation results as a Pickled dataframe - in the event that a simulation fails mid-way, the results until that point will be available
partial_results = pd.DataFrame()
partial_results_file = f'''exports/system_model_v2/partial_results.pickle'''
partial_results.to_pickle(partial_results_file)

# Enabled or disable APT tests - these tests bypass the APT ML model, for quick model validation
enable_apt_tests = False

apt_tests = [
        {
            # Enable or disable a specific test
            'enable': True,
            # Configure the test parameters
            'params': {
                # Optimal values to override the APT model suggestions
                'optimal_values': {
                    'v_1': lambda timestep=0: 1000,
                    'v_2 + v_3': lambda timestep=0: 500,
                    'u_1': lambda timestep=0: 100,
                    'u_2': lambda timestep=0: 50
                }
            }
        },
        ## Alternative test cases:
        # {
        #     'enable': False,
        #     'params': {
        #         'optimal_values': {
        #             'v_1': lambda timestep=0, df=simulation_results_df: \
        #                 simulation_results_df.iloc[timestep]['optimal_values'].get('v_1', historical_initial_state['v_1']),
        #             'v_2 + v_3': lambda timestep=0, df=simulation_results_df: \
        #                 simulation_results_df.iloc[timestep]['optimal_values'].get('v_2 + v_3', historical_initial_state['v_2 + v_3']),
        #             'u_1': lambda timestep=0, df=simulation_results_df: \
        #                 simulation_results_df.iloc[timestep]['optimal_values'].get('u_1', historical_initial_state['u_1']),
        #             'u_2': lambda timestep=0, df=simulation_results_df: \
        #                 simulation_results_df.iloc[timestep]['optimal_values'].get('u_2', historical_initial_state['u_2'])
        #         }
        #     }
        # },
        # {
        #     'enable': False,
        #     'params': {
        #         'optimal_values': {
        #             'v_1': lambda timestep=0: historical_initial_state['v_1'],
        #             'v_2 + v_3': lambda timestep=0: historical_initial_state['v_2 + v_3'],
        #             'u_1': lambda timestep=0: historical_initial_state['u_1'],
        #             'u_2': lambda timestep=0: historical_initial_state['u_2']
        #         }
        #     }
        # },
        # {
        #     'enable': False,
        #     'params': {
        #         'optimal_values': {
        #             'v_1': lambda timestep=0: 500,
        #             'v_2 + v_3': lambda timestep=0: 1000,
        #             'u_1': lambda timestep=0: 50,
        #             'u_2': lambda timestep=0: 100
        #         }
        #     }
        # }
]

params = {
    # Admin parameters
    'test': apt_tests if enable_apt_tests else [{'enable': False}],
    'debug': [True], # Print debug messages (see APT model)
    'raise_on_assert': [False], # See assert_log() in utils.py
    'free_memory_states': [['cdps', 'events']],
    'partial_results': [partial_results_file],

    # Configuration options
    options.IntegralType.__name__: [options.IntegralType.LEAKY.value],

    # Exogenous states, loaded as parameter at every timestep - these are lambda functions, and have to be called
    'eth_price': [lambda timestep, df=debt_market_df: df.iloc[timestep].rho_star],
    'seconds_passed': [lambda timestep, df=debt_market_df: df.iloc[timestep].seconds_passed],

    # Time parameters
    'expected_blocktime': [15], # seconds
    'minumum_control_period': [lambda _timestep: 3600], # seconds
    'expected_control_delay': [lambda _timestep: 1200], # seconds
    
    # Controller parameters
    'controller_enabled': [True],
    'kp': [5e-7], # proportional term for the stability controller: units 1/USD
    'ki': [lambda control_period=3600: -1e-7 / control_period], # integral term for the stability controller: units 1/(USD*seconds)
    'alpha': [alpha], # in 1/RAY
    'error_term': [lambda target, measured: target - measured],
    
    # APT model
    'use_APT_ML_model': [True],
    'freeze_feature_vector': [False], # Use the same initial state as the feature vector for each timestep
    'interest_rate': [1.0], # Real-world expected interest rate, for determining profitable arbitrage opportunities
    
    'root_function': [glf],
    'callback': [glf_continue_callback],
    'model': [model],
    'features': [features_ml],
    'optvars': [optvars],
    'bounds': [[(xmin,debt_market_df[optvars].max()[i]) 
        for i,xmin in enumerate(debt_market_df[optvars].min())
    ]],
    'eth_price_mean': [eth_price_mean],
    'eth_returns_mean': [eth_returns_mean],
    'market_price_mean': [market_price_mean],

    # APT OLS model
    'alpha_0': [0],
    'alpha_1': [1],
    'beta_0': [1.0003953223600617],
    'beta_1': [0.6756295152422528],
    'beta_2': [3.86810578185312e-06],

    # CDP parameters
    'new_cdp_proportion': [0.5], # Proportion of v_1 or u_1 (collateral locked or debt drawn) from APT optimal values used to create new CDPs 
    'new_cdp_collateral': [2500], # The average CDP collateral for opening a new CDP, based on historical CDP collateral statistics
    'liquidation_ratio': [1.5], # Configure the liquidation ratio parameter e.g. 150%
    'liquidation_buffer': [2.0], # Configure the liquidation buffer parameter: the multiplier for the liquidation ratio, that users apply as a buffer
    'liquidation_penalty': [0], # Percentage added on top of collateral needed to liquidate CDP
    # Average CDP duration == 3 months: https://www.placeholder.vc/blog/2019/3/1/maker-network-report
    # The tuning of this parameter is probably off the average, because we don't have the CDP size distribution matched yet,
    # so although the individual CDPs could have an average debt age of 3 months, the larger CDPs likely had a longer debt age.
    'average_debt_age': [3 * (30 * 24 * 3600)], # delta t (seconds)

    # System parameters
    'stability_fee': [lambda timestep, df=debt_market_df: stability_fee], # per second interest rate (x% per month)
}
