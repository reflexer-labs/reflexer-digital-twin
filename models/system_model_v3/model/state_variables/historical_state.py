import pandas as pd
import numpy as np


# The full feature vector from the historical MakerDAO Dai dataset
features = [
    'beta', 'Q', 'v_1', 'v_2 + v_3', 
    'D_1', 'u_1', 'u_2', 'u_3', 'u_2 + u_3', 
    'D_2', 'w_1', 'w_2', 'w_3', 'w_2 + w_3',
    'D'
]

# Import the historical MakerDAO market data CSV file
debt_market_df = pd.read_csv('models/market_model/data/debt_market_df.csv', index_col='date', parse_dates=True)

# Create a new column for `seconds_passed`, setting to 1 day in seconds - the sampling period available for historical data
# debt_market_df.insert(0, 'seconds_passed', 24 * 3600)


# Create a dataframe for the market price
market_price_df = pd.DataFrame(debt_market_df['p'])
# Calculate the mean market price
market_price_mean = np.mean(market_price_df.to_numpy().flatten())

env_process_df = pd.read_csv('models/market_model/data/ETH_1H.csv', index_col='Date', parse_dates=True)
env_process_df.insert(0, 'seconds_passed', 3600)
env_process_df = env_process_df.sort_values(by=['Date'])

start_date = '2017-09-14'
end_date = '2018-09-12'

env_process_df = env_process_df.loc[start_date:end_date]

# Create a dataframe for the ETH price
eth_price_df = pd.DataFrame(env_process_df['Open'])
# Calculate the mean ETH price
eth_price_mean = np.mean(eth_price_df.to_numpy().flatten())

# Set the initial ETH price state
eth_price = eth_price_df.iloc[0]['Open']

# Calculate the ETH returns and gross returns, for the equation to find the root of non-arbitrage condition
eth_returns = ((eth_price_df - eth_price_df.shift(1)) / eth_price_df.shift(1)).to_numpy().flatten()
eth_gross_returns = (eth_price_df / eth_price_df.shift(1)).to_numpy().flatten()

# Calculate the mean ETH returns
eth_returns_mean = np.mean(eth_returns[1:])
