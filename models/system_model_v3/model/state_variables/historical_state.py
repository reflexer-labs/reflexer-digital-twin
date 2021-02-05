import pandas as pd
import numpy as np


eth_price_df = pd.read_csv('models/system_model_v3/data/eth_prices.csv', index_col=0)

# Set the initial ETH price state
eth_price = eth_price_df["0"].iloc[0]
