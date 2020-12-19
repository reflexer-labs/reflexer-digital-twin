# APT market model functional stubs for incorporation into cadCAD RAI simulation



import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from autosklearn.regression import AutoSklearnRegressor
from autosklearn.metrics import mean_squared_error as auto_mean_squared_error
from pprint import pprint
import matplotlib.pyplot as plt
import math
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLSResults
from scipy.misc import derivative
import numpy as np
import seaborn as sns
import pickle

# 1. Debt market regression to create market model feature setup 
# ML approach based upon work from Markus & Zargham

def fitmodel(data_to_fit, 
             data_to_predict, 
             target_col,
             features=None, 
             verbose=False, 
             test_size=0.33
            ):
    if not features:
        features = ['beta', 'Q', 'v_1', 'v_2 + v_3', 
                    'D_1', 'u_1', 'u_2', 'u_3', 'u_2 + u_3', 
                    'D_2', 'w_1', 'w_2', 'w_3', 'w_2 + w_3',
                    'D']
    target = data_to_fit[target_col].copy()
    
    data_to_fit = data_to_fit[features]
    data_to_predict = data_to_predict[features]
    
    X_train, X_test, y_train, y_test = train_test_split(data_to_fit, target, test_size=test_size, random_state=1)
    
    model = AutoSklearnRegressor(time_left_for_this_task=5*60, 
                                 per_run_time_limit=30, 
                                 n_jobs=8,
                                 resampling_strategy='cv',
                                 resampling_strategy_arguments={'folds':5}
                                )
    model.fit(X_train, y_train)
    if verbose:
        print(model.sprint_statistics())
        models = model.get_models_with_weights()
        for m in models:
            print({m[0]: m[1].config['regressor:__choice__']})
    return model, model.predict(data_to_predict), y_test, model.predict(X_test)

def get_model_summary(model):
    result = []
    models = model.get_models_with_weights()
    for m in models:
        result.append((m[0],m[1].config['regressor:__choice__']))
    return result
    
# 2. OLS regression using feature output, ETH price and liquidity demand proxy

    
if __name__ == "__main__":

    compute_features = False
    compute_regression = False
    analyze_system = True
    
    debt_market_df = pd.read_csv('data/debt_market_df.csv', index_col='date', parse_dates=True)
    market_price = pd.DataFrame(debt_market_df['p'])
    eth_price = pd.DataFrame(debt_market_df['rho_star'])
    
    market_returns = np.log(market_price/market_price.shift(1))
    eth_returns = np.log(eth_price/eth_price.shift(1)).to_numpy()
    
    features = ['beta', 'Q', 'v_1', 'v_2 + v_3', 
                    'D_1', 'u_1', 'u_2', 'u_3', 'u_2 + u_3', 
                    'D_2', 'w_1', 'w_2', 'w_3', 'w_2 + w_3',
                    'D']

    if compute_features:

        print('Fitting model using 66% of the data for training')
        model, full_prediction, y_test, predicted_y_test = fitmodel(
                    data_to_fit = debt_market_df, 
                    data_to_predict = debt_market_df,
                    target_col = 'p',
                    features = features,
                    verbose=True,
                    test_size=0.34)
        r2 = r2_score(y_test,predicted_y_test)
        print(f'R2: {r2}')
        market_price[f'p_hat R2={r2:.2f}'] = full_prediction
        pprint(get_model_summary(model))
        sns.regplot(y_test, predicted_y_test).set_title('Target vs Predictions');
        print('---')
        
        pickle.dump(model, open('apt_debt_model.pickle', 'wb'))
    
    if compute_regression:
    
        if not compute_features:
            model = pickle.load(open('apt_debt_model.pickle', 'rb'))
            independent_vars = debt_market_df[features]
            full_prediction = pd.DataFrame(model.predict(independent_vars))
        
        feature_returns = np.log(full_prediction/full_prediction.shift(1)).to_numpy()
        
        # to do: estimated liquidity demand from single collateral DAI
        X = np.stack((feature_returns, eth_returns))  
        #X = sm.add_constant(np.transpose(X))
        X = np.transpose(X)[0,:,:]
        #X = feature_returns.join(eth_returns)
        
        OLSmodel = sm.OLS(market_returns, X, missing='drop')
        results = OLSmodel.fit()
        print(results.summary())
        
        results.save('apt_market_model.pickle')
    
    if analyze_system:
        
        if not compute_features:
            model = pickle.load(open('apt_debt_model.pickle', 'rb'))
            independent_vars = debt_market_df[features]
            full_prediction = pd.DataFrame(model.predict(independent_vars))
            
        if not compute_regression:
            OLSres = OLSResults.load('apt_market_model.pickle')
            
        def apt_response(x_name, feature_vals, test_index, p, dp):
            
            # define gradient (central difference)
            def gradient(f, x, dx = 1e-4):
                # convert x dataframe to Series
                y = x.iloc[0]
                n = len(y)
                grad = np.zeros(n)
                for j in range(n):
                    dx_i = abs(y[j])*dx if y[j] != 0 else dx
                    x_pos = [ x_i if i != j else x_i + dx_i for i, x_i in enumerate(y) ]
                    x_neg = [ x_i if i != j else x_i - dx_i for i, x_i in enumerate(y) ]
                    # convert back to dataframe for f evaluation
                    x_pos = pd.DataFrame(x_pos).T
                    x_neg = pd.DataFrame(x_neg).T
                    f_pos = f(x_pos)
                    f_neg = f(x_neg)
                    grad[j] = ( f_pos[0] - f_neg[0] ) / ( 2 * dx_i )
                return grad
            
            # convert price and dp to numpy
            p = p.to_numpy()
            dp = dp.to_numpy()
            
            # get value and gradient at point of interest
            model_value = model.predict(feature_vals)
            model_grad = gradient(model.predict, feature_vals)
            
            # invert gradient (where zero, infinities will appear)
            inv_grad = 1/model_grad
            
            # get index of variable of interest
            feature_index = feature_vals.columns.get_loc(x_name)
            
            # rescale price from regression results
            dp = ( dp - p * OLSres.params[1]*eth_returns[test_index] -
                p * OLSres.resid[test_index] ) / OLSres.params[0]
            
            # zero change for infinities (indicates no change in price for var at this point)
            change = inv_grad[feature_index] if not math.isinf(inv_grad[feature_index]) else 0

            # return change in target variable given observed change in market price 
            dx = ( model_value / p ) * change * dp
            
            return dx
            
        print('u_2 + u_3: ', apt_response('u_2 + u_3', 
                           pd.DataFrame(independent_vars.iloc[200]).T, 
                           200,
                           market_price.iloc[200],
                           (market_price.iloc[201] - market_price.iloc[200])
        ))