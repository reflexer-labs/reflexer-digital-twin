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
debt_market_df.insert(0, 'seconds_passed', 24 * 3600)

# Select the start date from historical data to use as the model initial state

# Select the start date; historical state with a minimal pool of CDP collateral and debt
start_date = '2017-12-25'

# Build a feature vector from the historical dataset at the start_date, to be used as the model initial state
historical_initial_state = {k: debt_market_df.loc[start_date][k] for k in features}

# Pre-process the historical data

# Create a dataframe for the ETH price
eth_price_df = pd.DataFrame(debt_market_df['rho_star'])
# Calculate the mean ETH price
eth_price_mean = np.mean(eth_price_df.to_numpy().flatten())

# Create a dataframe for the market price
market_price_df = pd.DataFrame(debt_market_df['p'])
# Calculate the mean market price
market_price_mean = np.mean(market_price_df.to_numpy().flatten())

# Calculate the ETH returns and gross returns, for the equation to find the root of non-arbitrage condition
eth_returns = ((eth_price_df - eth_price_df.shift(1)) / eth_price_df.shift(1)).to_numpy().flatten()
eth_gross_returns = (eth_price_df / eth_price_df.shift(1)).to_numpy().flatten()

# Calculate the mean ETH returns
eth_returns_mean = np.mean(eth_returns[1:])

# Set the initial ETH price state
eth_price = eth_price_df.loc[start_date][0]
# Set the initial market price state
market_price = debt_market_df.loc[start_date]['p']
# Set the initial target price, in Dollars
target_price = 1.0

# Configure the initial stability fee parameter, as a scaled version of the historical data beta at the start date
stability_fee = (historical_initial_state['beta'] * 30 / 365) / (30 * 24 * 3600)
