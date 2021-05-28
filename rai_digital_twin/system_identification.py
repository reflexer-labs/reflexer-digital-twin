from dataclasses import dataclass
from typing import Iterable, Union
from numpy import ndarray
from statsmodels.tsa.api import VAR
import pandas as pd
from sklearn.preprocessing import PowerTransformer

from rai_digital_twin.types import ActionState, ControllerState, ETH, ETH_per_RAI, OptimalAction, Percentage, RAI, TokenState, TransformedTokenState, USD_per_ETH, USD_per_RAI, UserActionParams
from rai_digital_twin.types import coordinate_transform, reverse_coordinate_transform


def arbitrageur_action_options(RAI_balance: RAI,
                               ETH_balance: ETH,
                               liquidation_price: ETH_per_RAI,
                               uniswap_fee: Percentage) -> OptimalAction:
    K = (RAI_balance * ETH_balance * (1 - uniswap_fee))
    optimal_borrow = (K / liquidation_price) ** 0.5
    optimal_repay = (K * liquidation_price) ** 0.5
    return OptimalAction(optimal_borrow, optimal_repay)


def compute_arbitrageur_action(token_state: TokenState,
                               fee_survival: Percentage,
                               liquidation_price: ETH_per_RAI,
                               expensive_threshold: Percentage,
                               cheap_threshold: Percentage,
                               relative_redemption_price: Percentage,
                               optimal_actions) -> TokenState:
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


def arbitrageur_action(token_state: TokenState,
                       controller_state: ControllerState,
                       market_price: USD_per_RAI,
                       eth_price: USD_per_ETH,
                       params: UserActionParams) -> TokenState:

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
                                                 liquidation_price,
                                                 params.uniswap_fee)

    action = compute_arbitrageur_action(token_state,
                                        fee_survival,
                                        liquidation_price,
                                        expensive_threshold,
                                        cheap_threshold,
                                        relative_redemption_price,
                                        optimal_actions)

    # * (token_state.eth_reserve / action.eth_reserve * params.intensity)
    return action


def VAR_prediction(errors: list[list[float]],
                   lag: int = 15) -> ndarray:
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


def action_errors(past_states: list[ActionState],
                  params: UserActionParams,
                  ewm_alpha=0.8) -> Iterable[TransformedTokenState]:

    if len(past_states) > 1:
        # First state
        last_token_state: TokenState = past_states[0].token_state

        # Retrieve a dataframe of all past token states
        token_state_list = [state.token_state
                            for state in past_states]
        token_state_df = pd.DataFrame(token_state_list)

        # Compute the EWM difference between states
        optimal_actions_df = (token_state_df
                              .ewm(alpha=ewm_alpha)
                              .mean()
                              .diff()
                              .to_dict(orient='records')
                              [1:])
        optimal_actions = [TokenState(**row) for row in optimal_actions_df]

        # Iterate
        for i, state in enumerate(past_states[1:]):
            token_state = state.token_state

            # Compute real and optimal actions
            real_action = token_state - last_token_state
            optimal_action = optimal_actions[i]

            transform_args = (token_state,
                              state.pid_state,
                              params,
                              state.eth_price)

            # Transform real and optimal actions
            transformed_real_action = coordinate_transform(real_action,
                                                           *transform_args)
            transformed_optimal_action = coordinate_transform(optimal_action,
                                                              *transform_args)

            # Compute error
            error = transformed_optimal_action - transformed_real_action
            last_token_state = token_state

            # Yield
            yield error
    else:
        raise Exception("Insufficient data points")


def fit_predict_action(past_states: list[ActionState],
                       action_params: UserActionParams,
                       ewm_alpha: float = 0.8,
                       var_lag: int = 15) -> Union[TokenState, None]:
    """
    Steps:
    1. Retrieve historical arbitrageur actions
    2. Transform historical arbitrageur actions
    3. Transform historical real actions
    4. Fit VAR model to the historical error
    5. Predict next action
    6. Apply next action to state
    """
    if type(past_states) == list:
        if len(past_states) > 0:
            state = past_states[-1]

            # Retrieve errors on the transformed coordinates
            errors = list(action_errors(past_states,
                                        action_params,
                                        ewm_alpha=ewm_alpha))
            errors = pd.DataFrame(errors).dropna().values  # HACK

            # Perform a Power Transformation
            transformer = PowerTransformer()
            transformed_errors = transformer.fit_transform(errors)

            # Train VAR model and generate prediction
            transformed_prediction = VAR_prediction(transformed_errors,
                                                    var_lag)
            
            transformed_prediction = transformed_prediction.reshape(1, -1)
            # Go back to the transformed coordinates
            prediction = transformer.inverse_transform(transformed_prediction)
            prediction = prediction.tolist()[0] # HACK for making sense of numpy
            transformed_new_action = TransformedTokenState(*prediction)

            # Go Back to the original coordinates
            transform_args = (state.token_state,
                              state.pid_state,
                              action_params,
                              state.eth_price)
            new_action = reverse_coordinate_transform(transformed_new_action,
                                                      *transform_args)
            return new_action
        else:
            return None
    else:
        return None
