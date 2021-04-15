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
    mean_cdp_collateral: float
    median_cdp_collateral: float


class OptimalValues(TypedDict):
    u_1: RAI
    u_2: RAI
    v_1: RAI
    v_2: RAI