
def initialize_redemption_price(params, substep, state_history, state, policy_input):
    if state['timestep'] == 0 and params['rescale_redemption_price']:
        initial_redemption_price = state['redemption_price'] / params['liquidation_ratio']
    else:
        initial_redemption_price = state['redemption_price']
    return 'redemption_price', initial_redemption_price
