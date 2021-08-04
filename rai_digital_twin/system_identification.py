from dataclasses import dataclass
from typing import Iterable, Union
from numpy import ndarray
import numpy as np
from statsmodels.tsa.api import VAR
import pandas as pd
from sklearn.preprocessing import PowerTransformer, StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import make_pipeline
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neighbors import DistanceMetric
from sklearn.tree import DecisionTreeRegressor

from rai_digital_twin.types import ActionState, ControllerState, ETH, ETH_per_RAI, OptimalAction, Percentage, RAI, TokenState, TransformedTokenState, USD_per_ETH, USD_per_RAI, UserActionParams
from rai_digital_twin.types import coordinate_transform, reverse_coordinate_transform
from rai_digital_twin.types import TransformedTokenStatePlus
from rai_digital_twin.types import coordinate_transform_plus

"""
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

"""

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

def rf_prediction(diffs, lag=1, n_features=4):
    
    #diffs = diffs.rolling(window=lag, min_periods=1).mean()
    X = []
    y = []    
    dfs = [diffs]
    for i in range(lag):
        dfs.append(diffs.shift(i+1))
        
    shifted_df = pd.concat(dfs, axis=1)
    #shifted_df.iloc[:,n_features:] = shifted_df.iloc[:,n_features:].rolling(window=lag, min_periods=1).mean()

    for i, row in shifted_df.iloc[lag:].iterrows():
        y.append(row[:4])
        X.append(row[n_features:]) # shape = (,n_features * lag)
    
    X = np.array(X)
    y = np.array(y)
    
    #rf = RandomForestRegressor(100, n_jobs=-1)
    #rf = DecisionTreeRegressor(criterion='mse')
    #def token_state_dist(x, y, r_s, e_s, p_s):
    def token_state_dist(x, y, s_s):
        #x = s_s.transform(x[[0,1,6]].reshape(1,-1))
        #y = s_s.transform(y[[0,1,6]].reshape(1,-1))
        x = s_s.transform(x.reshape(1,-1))
        y = s_s.transform(y.reshape(1,-1))

        d1  = np.linalg.norm(x - y)
        return d1

    #s_s = StandardScaler().fit(X[:,[0,1,6]])
    s_s = StandardScaler().fit(X)
    rf = KNeighborsRegressor(n_neighbors=1, metric=token_state_dist,
                             #metric_params={'r_s':r_s, 'e_s': e_s, 'p_s': p_s},
                             metric_params={'s_s':s_s},
                             weights='distance')
    ss = StandardScaler()
    #X = ss.fit_transform(X)

    rf.fit(X, y)
    
    final_x = shifted_df.iloc[-1,:lag*n_features].values.reshape(1,-1)
    #final_x = ss.transform(final_x)
    pred = rf.predict(final_x)
    
    return pred[0]

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
            #yield error
            yield transformed_real_action
    else:
        raise Exception("Insufficient data points")

def action_token_states(past_states: list[ActionState],
                  params: UserActionParams,
                  ewm_alpha=0.8) -> Iterable[TokenState]:

    if len(past_states) > 1:
        # First state
        last_token_state: TokenState = past_states[0].token_state


        # Iterate
        for i, state in enumerate(past_states[1:]):
            token_state = state.token_state

            # Compute real and optimal actions
            real_action = token_state - last_token_state
            last_token_state = token_state

            # Yield
            yield real_action
            #yield transformed_real_action
    else:
        raise Exception("Insufficient data points")

def action_state_diffs(past_states: list[ActionState],
                  params: UserActionParams,
                  ewm_alpha=0.8) -> Iterable[TokenState]:

    if len(past_states) > 1:
        # First state
        last_action_state: ActionState = past_states[0]


        # Iterate
        for i, action_state in enumerate(past_states[1:]):

            # Compute real and optimal actions
            real_action = action_state - last_action_state
            last_action_state = action_state

            # Yield
            yield real_action
    else:
        raise Exception("Insufficient data points")

def action_state_diffs_ma(past_states: list[ActionState],
                  params: UserActionParams,
                  ewm_alpha=0.8) -> Iterable[TokenState]:

    if len(past_states) > 1:
        # First state
        diffs_expanded = []
        for action_state in past_states:
            diffs_expanded.append([action_state.token_state.rai_reserve, action_state.token_state.eth_reserve,
                                   action_state.token_state.rai_debt, action_state.token_state.eth_locked,
                                   action_state.pid_state.redemption_price, action_state.pid_state.proportional_error,
                                   action_state.eth_price, action_state.market_price])

        action_state_df = pd.DataFrame(diffs_expanded)

        # Compute the EWM difference between states
        #optimal_actions_df = action_state_df.ewm(alpha=ewm_alpha).mean().diff()[1:]
        optimal_actions_df = action_state_df.rolling(window=10, min_periods=1).mean().diff()[1:]
                              #.to_dict(orient='records')
                              #[1:])

        optimal_actions = [ActionState(TokenState(row[0], row[1], row[2], row[3]),
                                       ControllerState(row[4], 0, row[5], 0),
                                       row[7], row[6]) for i, row in optimal_actions_df.iterrows()]

        # Iterate
        for i, action_state in enumerate(past_states[2:]):

            # Compute error
            diff = action_state - optimal_actions[i-1]

            # Yield
            yield diff
    else:
        raise Exception("Insufficient data points")


def states_features(past_states: list[ActionState],
                    params: UserActionParams,
                    ewm_alpha=0.8) -> Iterable[TransformedTokenStatePlus]:

    if len(past_states) > 1:
        # Iterate
        for i, action_state in enumerate(past_states[1:]):
            #state = coordinate_transform_plus(action_state, action_state, params)

            # Yield
            yield action_state
    else:
        raise Exception("Insufficient data points")


def fit_predict_action(past_states: list[ActionState],
                       action_params: UserActionParams,
                       model: str = 'ewm',
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
            #diffs = list(states_features(past_states,

            if model == 'var':
                # Retrieve errors on the transformed coordinates
                errors = list(action_errors(past_states,
                                            action_params,
                                            ewm_alpha=ewm_alpha))
                errors = pd.DataFrame(errors).values

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

                # Go back to the original coordinates
                transform_args = (state.token_state,
                                  state.pid_state,
                                  action_params,
                                  state.eth_price)
                new_action = reverse_coordinate_transform(transformed_new_action,
                                                          *transform_args)
                return new_action

            elif model == 'rf':
                # Retrieve errors on the transformed coordinates
                errors = list(action_errors(past_states,
                                            action_params,
                                            ewm_alpha=ewm_alpha))
                errors = pd.DataFrame(errors).values

                # Perform a Power Transformation
                transformer = PowerTransformer()
                transformed_errors = transformer.fit_transform(errors)
                transformed_errors = pd.DataFrame(transformed_errors)

                # Train VAR model and generate prediction
                transformed_prediction = rf_prediction(transformed_errors,
                                                        var_lag)

                transformed_prediction = transformed_prediction.reshape(1, -1)

                # Go back to the transformed coordinates
                prediction = transformer.inverse_transform(transformed_prediction)
                prediction = prediction.tolist()[0] # HACK for making sense of numpy
                transformed_new_action = TransformedTokenState(*prediction)

                # Go back to the original coordinates
                transform_args = (state.token_state,
                                  state.pid_state,
                                  action_params,
                                  state.eth_price)
                new_action = reverse_coordinate_transform(transformed_new_action,
                                                          *transform_args)
                return new_action

            elif model == 'rf2':
                    # Retrieve errors on the transformed coordinates
                diffs = list(action_state_diffs(past_states,
                                            action_params,
                                            ewm_alpha=ewm_alpha))
                diffs_expanded = []
                for action_state in diffs:
                    diffs_expanded.append([action_state.token_state.rai_reserve, action_state.token_state.eth_reserve,
                                           action_state.token_state.rai_debt, action_state.token_state.eth_locked,
                                           action_state.pid_state.redemption_price, action_state.pid_state.proportional_error,
                                           action_state.eth_price, action_state.market_price])
                                        
                diffs = pd.DataFrame(diffs_expanded)

                # Train RF model and generate prediction
                prediction = rf_prediction(diffs, var_lag, n_features=8)

                prediction = prediction.reshape(1, -1)

                # Go back to the transformed coordinates
                prediction = prediction.tolist()[0] # HACK for making sense of numpy
                new_action = TokenState(*prediction)
                return new_action

            return None
    else:
        return None
