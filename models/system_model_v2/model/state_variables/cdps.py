from .debt_market import *

# Based on CDP collateral statistics, calculate the total number of initial CDPs to be created
mean_cdp_collateral = 50 # dollars
genesis_cdp_count = int(eth_collateral / mean_cdp_collateral)

# Create a pool of initial CDPs
cdp_list = []
for i in range(genesis_cdp_count):
    cdp_list.append({
        'open': 1, # Is the CDP open or closed? True/False == 1/0 for integer/float series
        'time': 0, # How long the CDP has been open for
        # Divide the initial state of ETH collateral and principal debt among the initial CDPs
        'locked': eth_collateral / genesis_cdp_count,
        'drawn': principal_debt / genesis_cdp_count,
        'wiped': 0.0, # Principal debt wiped
        'freed': 0.0, # ETH collateral freed
        'w_wiped': 0.0, # Accrued interest wiped
        'v_bitten': 0.0, # ETH collateral bitten (liquidated)
        'u_bitten': 0.0, # Principal debt bitten
        'w_bitten': 0.0, # Accrued interest bitten
        'dripped': 0.0 # Total interest accrued
    })

cdps = pd.DataFrame(cdp_list)
