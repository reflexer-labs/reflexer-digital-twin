from dataclasses import dataclass
from enum import Enum

# Units

# Measurements Units

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

TimestepDict = list[dict[str, object]]
class GovernanceEventKind(Enum):
    change_pid_params = 1

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

@dataclass(frozen=True)
class ControllerParams():
    kp: Per_USD
    ki: Per_USD_Seconds
    leaky_factor: Percentage
    period: Seconds
    enabled: bool

@dataclass(frozen=True)
class ControllerState():
    redemption_price: USD_per_RAI
    redemption_rate: Percentage
    proportional_error: USD_per_RAI
    integral_error: USD_Seconds_per_RAI

@dataclass(frozen=True)
class TokenState():
    rai_reserve: RAI
    eth_reserve: ETH
    rai_debt: RAI
    eth_locked: ETH
