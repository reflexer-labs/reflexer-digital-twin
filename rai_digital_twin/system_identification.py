from statsmodels.tsa.api import VARMAX, VAR
import pandas as pd

from rai_digital_twin.types import TokenState, TransformedTokenState, UserActionParams


def get_aggregated_arbitrageur_decision(params,
                                        state) -> TokenState:

    # This Boolean indicates whether or not the arbitrageur is rationally considering
    # borrowing to the liquidation ratio limit. If TRUE, arbitrage opportunities are less
    # frequent when RAI is expensive and more frequent when RAI is cheap. If FALSE, only
    # the difference in market and redemption prices (net of Uniswap fee) matters for trading,
    # which may conform more to individual trader expectations and behavior.
    consider_liquidation_ratio = params['arbitrageur_considers_liquidation_ratio']

    # These are the states of the SAFE balances in aggregate & its fixed parameters
    total_borrowed = state['SAFE_Debt']  # D
    total_collateral = state['SAFE_Collateral']  # Q
    liquidation_ratio = params['liquidation_ratio']
    debt_ceiling = params['debt_ceiling']

    # These are the states of the Uniswap secondary market balances and its fee
    RAI_balance = state['RAI_balance']  # R_Rai
    ETH_balance = state['ETH_balance']  # R_Eth
    uniswap_fee = params['uniswap_fee']

    # These are the prices of RAI in USD/RAI for SAFE redemption and the market price oracle, resp.
    redemption_price = state['target_price']  # $p^r_{U/R}
    market_price = state['market_price']  # p_{U/R} > 0

    # This is the price of ETH in USD/ETH
    eth_price = state['eth_price']  # p_{U/E}

    # These functions define the optimal borrowing/repayment decisions of the aggregated arbitrageur

    def g1(RAI_balance, ETH_balance, uniswap_fee, liquidation_ratio, redemption_price):
        return ((eth_price * RAI_balance * ETH_balance * (1 - uniswap_fee)) / (liquidation_ratio * redemption_price)) ** 0.5

    def g2(RAI_balance, ETH_balance, uniswap_fee, liquidation_ratio, redemption_price):
        return (RAI_balance * ETH_balance * (1 - uniswap_fee) * liquidation_ratio * (redemption_price / eth_price)) ** 0.5

    # This Boolean resolves to TRUE if the agg. arb. acts this timestep when RAI is expensive
    # on the secondary market
    expensive_RAI_on_secondary_market = \
        redemption_price < ((1 - uniswap_fee) / liquidation_ratio) * market_price  \
        if consider_liquidation_ratio \
        else redemption_price < (1 - uniswap_fee) * market_price

    # This Boolean resolves to TRUE if the agg. arb. acts this timestep when RAI is cheap
    # on the secondary market
    cheap_RAI_on_secondary_market = \
        redemption_price > (1 / ((1 - uniswap_fee) * liquidation_ratio)) * market_price  \
        if consider_liquidation_ratio \
        else redemption_price > (1 / (1 - uniswap_fee)) * market_price

    if expensive_RAI_on_secondary_market:
        '''
        Expensive RAI on Uni:
        (put ETH from pocket into additional collateral in SAFE)
        draw RAI from SAFE -> Uni
        ETH from Uni -> into pocket
        '''

        _g1 = g1(RAI_balance, ETH_balance, uniswap_fee,
                 liquidation_ratio, redemption_price)
        d = (_g1 - RAI_balance) / (1 - uniswap_fee)  # should be \geq 0
        q = ((liquidation_ratio * redemption_price) /
             eth_price) * (total_borrowed + d) - total_collateral  # should be \geq 0
        z = -(ETH_balance * d * (1 - uniswap_fee)) / \
            (RAI_balance + d * (1 - uniswap_fee))  # should be leq 0
        r = d  # should be \geq 0

    elif cheap_RAI_on_secondary_market:
        '''
        Cheap RAI on Uni:
        ETH out of pocket -> Uni
        RAI from UNI -> SAFE to wipe debt
        (and collect collateral ETH from SAFE into pocket)
        '''

        _g2 = g2(RAI_balance, ETH_balance, uniswap_fee,
                 liquidation_ratio, redemption_price)
        z = (_g2 - ETH_balance) / (1 - uniswap_fee)  # should be \geq 0
        r = -(RAI_balance * z * (1 - uniswap_fee)) / \
            (ETH_balance + z * (1 - uniswap_fee))  # should be \leq 0
        d = r  # should be \leq 0
        q = ((liquidation_ratio * redemption_price /
             eth_price) * (total_borrowed + d) - total_collateral)  # should be \leq 0
    else:
        pass

    return TokenState(r, z, d, q)

# function to create coordinate transformations


def coordinate_transformations(params,
                               df,
                               Q,
                               R_eth,
                               R_rai,
                               D,
                               RedemptionPrice,
                               EthPrice):
    '''
    Description:
    Function that takes in pandas dataframe and the names of columns

    Parameters:
    df: pandas dataframe containing states information
    Q: dataframe column name
    R_eth: dataframe column name
    R_rai: dataframe column name
    D: dataframe column name
    RedemptionPrice: dataframe column name
    EthPrice: dataframe column name

    Returns: Pandas dataframe with alpha, beta, gamma, delta transformed values

    Example:

    coordinate_transformations(params,states,'collateral','EthInUniswap','RaiInUniswap',
                           'RaiDrawnFromSAFEs','RedemptionPrice','ETH Price (OSM)')[['alpha','beta','gamma','delta']]
    '''

    # Calculate alpha
    # Delta Debt
    d = df[D].diff()
    d.fillna(0, inplace=True)
    df['d'] = d

    # delta_rai_debt_scaled
    df['alpha'] = df['d'] / params['debt_ceiling']

    # calculate beta
    # LiqRatio * RedPrice / EthPrice -> LiqPrice in ETH/RAI
    df['C_o'] = (df[RedemptionPrice]/df[EthPrice]) * \
        params['liquidation_ratio']

    # Delta ETH collateral
    q = df[Q].diff()
    q.fillna(0, inplace=True)

    # Delta ETH collateral
    df['q'] = q

    # LiqPrice * TotalDebt - TotalCollateral -> GlobalLiqSurplus
    df['C_1'] = (df['C_o'] * df[D]) - df[Q]

    # [DeltaCollateral - (LiqPrice * DeltaDebt)] / GlobalLiqSurplus
    # -> DeltaLiqSurplus / GlobalLiqSurplus
    # ->
    df['beta'] = (df['q'] - (df['C_o']*df['d'])) / df['C_1']

    # calculate gamma
    # Delta RAI reserve
    r = df[R_rai].diff()
    r.fillna(0, inplace=True)
    df['r'] = r

    #
    df['gamma'] = df['r']/df[R_rai]

    # calculate delta
    z = df[R_eth].diff()
    z.fillna(0, inplace=True)
    df['z'] = z

    df['delta'] = df['z']/df[R_eth]

    return df


def create_transformed_errors(transformed_states, transformed_arbitrageur):
    '''
    Description:
    Function for taking two pandas dataframes of transformed states and taking the difference
    to produce an error dataframe

    Parameters:
    transformed_states: pandas dataframe with alpha, beta, gamma, and delta features
    transformed_arbitrageur: pandas dataframe with alpha, beta, gamma, and delta features

    Returns:
    error pandas dataframe

    '''
    alpha_diff = transformed_states['alpha'] - transformed_arbitrageur['alpha']
    beta_diff = transformed_states['beta'] - transformed_arbitrageur['beta']
    gamma_diff = transformed_states['gamma'] - transformed_arbitrageur['gamma']
    delta_diff = transformed_states['delta'] - transformed_arbitrageur['delta']

    e_u = pd.DataFrame(alpha_diff)
    e_u['beta'] = beta_diff
    e_u['gamma'] = gamma_diff
    e_u['delta'] = delta_diff

    e_u = e_u.astype(float)

    return e_u


def VARMAX_fit(e_u,
               RedemptionPriceError,
               lag=1) -> TransformedTokenState:
    '''
    Description:
    Function to train and forecast a VARMAX model one step into the future

    Parameters:
    e_u: errors pandas dataframe
    RedemptionPriceErrorPrevious: 1d Numpy array of RedemptionPriceError values
    newRedemptionPriceError: exogenous latest redemption price error signal - float
    lag: number of autoregressive lags. Default is 1

    Returns:

    Example

    '''
    # instantiate the VARMAX model object from statsmodels
    model = VARMAX(endog=e_u.values,
                   exog=RedemptionPriceError,
                   initialization='approximate_diffuse',
                   measurement_error=True)

    # fit model with determined lag values
    results = model.fit(order=(lag, 0),
                        maxiter=1  # HACK
                        )

    return results


def inverse_transformation_and_state_update(Y_pred: TokenState,
                                            state: dict[str, float],
                                            params: UserActionParams) -> TokenState:
    '''
    Description:
    Function to take system identification model prediction and invert transfrom and create new state

    Parameters:
    y_pred: numpy array of transformed state changes
    previous_state: pandas dataframe of previous state or 'current' state
    params: dictionary of system parameters

    Returns:
    pandas dataframe of new states

    Example:
    inverse_transformation_and_state_update(Y_pred,previous_state,params)
    '''

    d_star = Y_pred[0] * params['debt_ceiling']

    q_star = state['C_o'] * params['debt_ceiling']
    q_star *= Y_pred[0] + state['C_1'] * Y_pred[1]

    r_star = Y_pred[2] * state['gamma'] * state['RaiInUniswap']

    z_star = Y_pred[3] * state['delta'] * state['EthInUniswap']

    return TokenState(r_star, z_star, q_star, d_star)


def VAR_prediction(e_u,lag=1):
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
    model = VAR(e_u.values)
    # fit model with determined lag values
    results = model.fit(lag)
    lag_order = results.k_ar
    Y_pred = results.forecast(e_u.values[-lag_order:],1)
    return Y_pred[0]


def prepare_model():

    return None
    states = pd.read_csv('data/states.csv')
    del states['Unnamed: 0']
    states.head()
    # subset state variables for arbitrageur vector
    state_subset = states[['marketPriceUsd',
                           'RedemptionPrice',
                          'ETH Price (OSM)',
                           'collateral',
                           'EthInUniswap',
                           'RaiInUniswap',
                           'RaiDrawnFromSAFEs']]
    # map state data to arbitrageur vector fields
    state_subset.columns = ['market_price',
                            'target_price',
                            'eth_price',
                            'SAFE_Collateral',
                            'ETH_balance',
                            'RAI_balance',
                            'SAFE_Debt']
    # add additional state variables
    states['RedemptionPriceinEth'] = states['RedemptionPrice'] / \
        states['ETH Price (OSM)']
    states['RedemptionPriceError'] = states['RedemptionPrice'] - \
        states['marketPriceUsd']

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
    transformed = coordinate_transformations(params,
                                             states,
                                             'collateral',
                                             'EthInUniswap',
                                             'RaiInUniswap',
                                             'RaiDrawnFromSAFEs',
                                             'RedemptionPrice',
                                             'ETH Price (OSM)')
    transformed = transformed[['alpha', 'beta', 'gamma', 'delta']]
    local['RedemptionPrice'] = states['RedemptionPrice']
    local['ETH Price (OSM)'] = states['ETH Price (OSM)']

    transformed_arbitrageur = coordinate_transformations(params, local, 'Q', 'Reth', 'Rrai',
                                                         'D', 'RedemptionPrice', 'ETH Price (OSM)')[['alpha', 'beta', 'gamma', 'delta']]

    e_u = create_transformed_errors(transformed, transformed_arbitrageur)
    # split data between train and test (in production deployment, can remove)
    split_point = int(len(e_u) * .8)
    train = e_u.iloc[0:split_point]

    Y_pred = VAR_prediction(e_u)
    previous_state = states.iloc[train.index[-1]]
    result = inverse_transformation_and_state_update(Y_pred,
                                                     previous_state,
                                                     params)
    return result

def predict_real_action(state,
                        params) -> TokenState:
    pass


prepare_model()
