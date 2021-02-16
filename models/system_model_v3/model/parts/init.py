import random
import numpy as np


# Ensure all numpy RuntimeWarnings raise
np.seterr(divide='raise', over='raise', under='ignore')

def initialize_seed(params, substep, state_history, state):
    if state['timestep'] == 0:
        random.seed(a=f'{state["run"]}')
    return {}

def initialize_cdps(params, substep, state_history, state):
    if not state['cdps']:
        pass
    return {}

def initialize_target_price(params, substep, state_history, state, policy_input):
    initial_target_price = state['target_price'] / params['liquidation_ratio'] if state['timestep'] == 0 and params['rescale_target_price'] else state['target_price']
    return 'target_price', initial_target_price
