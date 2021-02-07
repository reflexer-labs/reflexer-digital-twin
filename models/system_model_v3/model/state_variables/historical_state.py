import pandas as pd
import numpy as np


eth_price_df = pd.read_csv('models/system_model_v3/data/eth_prices_mc.csv', index_col=0)

# Set the initial ETH price state
eth_price = eth_price_df["0"].iloc[0]

liquidity_demand_df = pd.read_csv('models/system_model_v3/data/liquidity_mc.csv', index_col=0)
token_swap_df = pd.read_csv('models/system_model_v3/data/buy_sell_mc.csv', index_col=0)
