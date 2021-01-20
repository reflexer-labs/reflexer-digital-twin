import scipy.stats as sts
import numpy as np


# Cheap RAI on Uni:
# ETH out of pocket -> Uni
# RAI from UNI -> CDP to wipe debt
# (and collect collteral ETH from CDP into pocket)

# Expensive RAI on Uni:
# (put ETH from pocket into additional collateral in CDP)
# draw RAI from CDP -> Uni
# ETH from Uni -> into pocket


# TODO: remove
# def update_market_price(params, substep, state_history, state, policy_input):
#     return "market_price", clearing_price
