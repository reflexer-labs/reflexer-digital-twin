# %%

import sys
import pandas as pd
import numpy as np
%load_ext autotime

# %%
sys.path.append("..")

# %%
from rai_digital_twin.types import ControllerState, TokenState

# %%
df = pd.read_csv('states.csv')
# %%
df.head(3)

# %%
df.columns
# %%
# %%
# %%


def row_to_controller_state(row: dict) -> ControllerState:
    return ControllerState(row.RedemptionPrice,
                           row.RedemptionRateAnnualizedRate,
                           np.nan,
                           np.nan)


def row_to_token_state(row: dict) -> TokenState:
    return TokenState(row.RaiInUniswap,
                      row.RaiInUniswap,
                      row.debt,
                      row.collateral)


# For validation only
pid_states = df.apply(row_to_controller_state, axis=1).tolist()
token_states = df.apply(row_to_token_state, axis=1).tolist()

# %%
EXOGENOUS_COLS = {'marketPriceEth': 'eth_price',
                  'marketPriceUsd': 'market_price'}

exogenous_data = (df.loc[:, EXOGENOUS_COLS.keys()]
                  .rename(columns=EXOGENOUS_COLS)
                  .to_dict(orient='records'))

# %%

# %%

# %%
