from statsmodels.tsa.api import VAR
import pandas as pd

from rai_digital_twin.types import ControllerState, ETH, ETH_per_RAI, OptimalAction, Percentage, RAI, TokenState, TransformedTokenState, USD_per_ETH, USD_per_RAI, UserActionParams
from rai_digital_twin.types import coordinate_transform, reverse_coordinate_transform


def arbitrageur_action_options(RAI_balance: RAI,
                               ETH_balance: ETH,
                               uniswap_fee: Percentage,
                               liquidation_price: ETH_per_RAI) -> OptimalAction:
    K = (RAI_balance * ETH_balance * (1 - uniswap_fee))
    optimal_borrow = (K / liquidation_price) ** 0.5
    optimal_repay = (K * liquidation_price) ** 0.5
    return OptimalAction(optimal_borrow, optimal_repay)


def arbitrageur_action(params: UserActionParams,
                       token_state: TokenState,
                       controller_state: ControllerState,
                       market_price: USD_per_RAI,
                       eth_price: USD_per_ETH) -> TokenState:

    fee_survival = (1 - params.uniswap_fee)
    liquidation_price: ETH_per_RAI = params.liquidation_ratio
    liquidation_price *= controller_state.redemption_price
    liquidation_price /= eth_price

    if params.consider_liquidation_ratio is True:
        expensive_threshold = fee_survival / params.liquidation_ratio
        cheap_threshold = fee_survival * params.liquidation_ratio

    else:
        expensive_threshold = fee_survival
        cheap_threshold = 1 / fee_survival

    relative_redemption_price = controller_state.redemption_price / market_price

    optimal_actions = arbitrageur_action_options(token_state.rai_reserve,
                                                 token_state.eth_reserve,
                                                 params.uniswap_fee,
                                                 liquidation_price)

    if relative_redemption_price <= expensive_threshold:
        action = optimal_actions.borrow
        d = (action - token_state.rai_reserve) / fee_survival
        q = liquidation_price * (token_state.rai_debt + d)
        q -= token_state.eth_locked
        z = -1 * (token_state.eth_reserve * d * fee_survival)
        z /= (token_state.rai_reserve + d * fee_survival)
        r = d
    elif relative_redemption_price >= cheap_threshold:
        action = optimal_actions.repay
        z = (action - token_state.eth_reserve) / fee_survival
        r = -1 * (token_state.rai_reserve * z * fee_survival)
        r /= (token_state.eth_reserve + z * fee_survival)
        d = r
        q = liquidation_price * (token_state.rai_debt + d)
        q -= token_state.eth_locked
    else:
        r = 0
        z = 0
        d = 0
        q = 0

    return TokenState(r, z, d, q)


def VAR_prediction(errors,
                   lag: int = 1):
    '''
    Description:
    Function to train and forecast a VAR model one step into the future
    Parameters:
    e_u: errors pandas dataframe
    lag: number of autoregressive lags. Default is 1
    Returns:
    Numpy array of transformed state changes
    Example
    VAR_prediction(e_u,6)    
    '''
    # instantiate the VAR model object from statsmodels
    model = VAR(errors)
    # fit model with determined lag values
    results = model.fit(lag)
    lag_order = results.k_ar
    Y_pred = results.forecast(errors[-lag_order:], 1)
    return Y_pred[0]


def prepare_model():
    states = pd.read_csv('data/states.csv')

    params = UserActionParams(1.45, 1e9, 0.003, True)
    # create list of u^* vectors
    values = []

    # iterate through real data to create u^* and save to values

    for i in range(0, len(state_subset)):
        values.append(get_aggregated_arbitrageur_decision(
            params, state_subset.loc[i]))

    # create historic u^* dataframe
    local = pd.DataFrame(values)
    local.columns = ['Q', 'D', 'Rrai', 'Reth']
    local.head()

    transformed = coordinate_transform(delta_state,
                                       global_state,
                                       controller_state,
                                       params,
                                       eth_price)

    transformed = transformed[['alpha', 'beta', 'gamma', 'delta']]
    local['RedemptionPrice'] = states['RedemptionPrice']
    local['ETH Price (OSM)'] = states['ETH Price (OSM)']

    e_u = transformed - transformed_arbitrageur

    Y_pred = VAR_prediction(e_u)
    result = inverse_transformation_and_state_update(Y_pred,
                                                     previous_state,
                                                     params)
    return result


def predict_real_action(state,
                        params) -> TokenState:
    pass
