# from .debt_market import eth_collateral
from models.system_model_v3.model.parts.debt_market import open_cdp_lock
from models.system_model_v3.model.state_variables.historical_state import eth_price
from models.system_model_v3.model.state_variables.system import target_price

import pandas as pd


liquidation_ratio = 1.45
liquidation_buffer = 2
liquidity_cdp_count = 0 # Set to zero to disable liquidity CDPs, and only use aggregate arbitrage CDP

uniswap_cdp_rai_balance = 5e6
uniswap_cdp_eth_collateral = uniswap_cdp_rai_balance * liquidation_ratio * liquidation_buffer * target_price / eth_price

arbitrage_cdp_rai_balance = 10e6
arbitrage_cdp_eth_collateral = arbitrage_cdp_rai_balance * liquidation_ratio * target_price / eth_price

# Create a pool of initial CDPs
cdp_list = []
for i in range(liquidity_cdp_count):
    cdp_list.append({
        'open': 1, # Is the CDP open or closed? True/False == 1/0 for integer/float series
        'arbitrage': 0,
        'time': 0, # How long the CDP has been open for
        # Divide the initial state of ETH collateral and principal debt among the initial CDPs
        'locked': uniswap_cdp_eth_collateral / liquidity_cdp_count,
        'drawn': uniswap_cdp_rai_balance / liquidity_cdp_count,
        'wiped': 0.0, # Principal debt wiped
        'freed': 0.0, # ETH collateral freed
        'w_wiped': 0.0, # Accrued interest wiped
        'v_bitten': 0.0, # ETH collateral bitten (liquidated)
        'u_bitten': 0.0, # Principal debt bitten
        'w_bitten': 0.0, # Accrued interest bitten
        'dripped': 0.0 # Total interest accrued
    })


cdp_list.append({**open_cdp_lock(arbitrage_cdp_eth_collateral, eth_price, target_price, liquidation_ratio), 'arbitrage': 1})

cdps = pd.DataFrame(cdp_list)

eth_collateral = cdps["locked"].sum()
principal_debt = cdps["drawn"].sum()

uniswap_rai_balance = principal_debt
uniswap_eth_balance = (uniswap_rai_balance * target_price) / eth_price
