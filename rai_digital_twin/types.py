from typing import NamedTuple, Dict, TypedDict
from enum import Enum
from typing import Dict, TypedDict, List

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

### cadCAD objects
Parameters = Dict[str, object]
State = Dict[str, object]
PolicyInput = Dict[str, object]

class InitialValue(NamedTuple):
    value: object
    unit: object

class Param(NamedTuple):
    value: object
    unit: object

class ParamSweep(NamedTuple):
    value: list[object]
    unit: object
## Structures
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
    drawn: float
    wiped: float
    freed: float
    w_wiped: float
    dripped: float
    v_bitten: float
    u_bitten: float
    w_bitten: float

class GovernanceEvent(NamedTuple):
    kind: str
    descriptor: dict

class UserAction(TypedDict):
    add_ETH_collateral: ETH
    add_RAI_debt: RAI
    RAI_delta: RAI
    ETH_delta: ETH
