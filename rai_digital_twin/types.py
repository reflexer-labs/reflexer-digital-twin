from dataclasses import dataclass

## Units

### Measurements Units

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

@dataclass(frozen=True)
class CDP_Metric():
    cdp_count: int
    open_cdp_count: int
    closed_cdp_count: int
    mean_cdp_collateral: ETH
    median_cdp_collateral: ETH


@dataclass()
class CDP():
    """
    Struct encapsulating a Collaterized Debt Position state for a single SAFE.
    """
    open: bool # Is it active?
    time: float #
    locked: ETH # Locked collateral
    drawn: RAI # 
    wiped: ETH #
    freed: ETH #
    w_wiped: float # Not used
    dripped: RAI # Accrued interest
    v_bitten: ETH #
    u_bitten: ETH #
    w_bitten: RAI #

@dataclass(frozen=True)
class GovernanceEvent():
    kind: str
    descriptor: dict

@dataclass(frozen=True)
class UserAction():
    add_ETH_collateral: ETH
    add_RAI_debt: RAI
    RAI_delta: RAI
    ETH_delta: ETH
