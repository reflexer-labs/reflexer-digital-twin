import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os.path
from os import path

import pandas as pd
import pickle
import numpy as np

import options

def load_debt_price_data(debt_price_source: options.DebtPriceSource):
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score
    from autosklearn.regression import AutoSklearnRegressor
    from autosklearn.metrics import mean_squared_error as auto_mean_squared_error

    test_dfs = []
    if debt_price_source == options.DebtPriceSource.EXTERNAL.value:
        if path.exists('./credentials/spreadsheet-credentials.json'):
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]

            credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials/spreadsheet-credentials.json', scope) # Your json file here
            gc = gspread.authorize(credentials)

            test_spreadsheet = gc.open('debt-price-test-data')
            print(gc.list_spreadsheet_files())

            worksheet_list = test_spreadsheet.worksheets()
            test_dfs = [pd.DataFrame(ws.get_all_values()[1:], columns=ws.get_all_values()[0]).copy() for ws in worksheet_list]
        else:
            debt_price_dataframe = pd.read_csv('./test/data/default_debt_price_source.csv')
            test_dfs = [debt_price_dataframe]
    elif debt_price_source == options.DebtPriceSource.DEBT_MARKET_MODEL.value:
        debt_market_df = pd.read_csv('market_model/debt_market_df.csv', index_col='date', parse_dates=True)
        loaded_model = pickle.load(open('market_model/debt_price_estimator.pickle', 'rb'))
        features = ['beta', 'Q', 'v_1', 'v_2 + v_3', 
                    'rho_star', 'C_star',
                    'D_1', 'u_1', 'u_2', 'u_3', 'u_2 + u_3', 
                    'D_2', 'w_1', 'w_2', 'w_3', 'w_2 + w_3',
                    'D']
        data_to_predict = debt_market_df[features]
        loaded_model_predictions = loaded_model.predict(data_to_predict)
        df = pd.DataFrame(loaded_model_predictions)
        df['debt_price'] = df[0]
        df['price_move'] = df['debt_price'].diff()
        df['price_move'][0] = df['debt_price'][0] - 1
        df.insert(0, 'seconds_passed', 24*3600)
        test_dfs = [df]
    return test_dfs

def step_dataframe(index, size, time_period=3600, length=720):
    '''
    Generates a dataframe given the `index` of the price_move, the `size` of the price_move,
    the `time_period` of the seconds_passed, and the `length` of the dataset
    '''
    return pd.DataFrame(
        np.array([[time_period, size] if i == index else [time_period, 0] for i in range(length)]),
        columns=['seconds_passed', 'price_move']
    )
