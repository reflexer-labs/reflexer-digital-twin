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

def initialize_redemption_price(params, substep, state_history, state, policy_input):
    if state['timestep'] == 0 and params['rescale_redemption_price']:
        initial_redemption_price = state['redemption_price'] / params['liquidation_ratio']
    else:
        initial_redemption_price = state['redemption_price']
    return 'redemption_price', initial_redemption_price
