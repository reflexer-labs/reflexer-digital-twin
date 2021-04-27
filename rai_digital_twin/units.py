from typing import Dict, TypedDict, List


Seconds = int
Height = int
ETH = float 
USD = float
RAI = float
exaRAI = float
UNI = float
ETH_per_USD = float
RAI_per_USD = float
USD_per_RAI = float
USD_Seconds_per_RAI = float
USD_per_Seconds = float
USD_per_ETH = float
Percentage_Per_Second = float
Percentage = float
Per_USD = float
Per_USD_Seconds = float
Per_RAY = float
Run = int
Timestep = int
Gwei = int

class CDP_Metric(TypedDict):
    cdp_count: int
    open_cdp_count: int
    closed_cdp_count: int
    mean_cdp_collateral: ETH
    median_cdp_collateral: ETH


class CDP(TypedDict):
    open: float
    time: float
    locked: float
    wiped: float
    freed: float
    w_wiped: float
    dripped: float
    v_bitten: float
    s_bitten: float
    w_bitten: float