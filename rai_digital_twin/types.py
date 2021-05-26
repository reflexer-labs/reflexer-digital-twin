from dataclasses import dataclass
from enum import Enum
import pandas as pd

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
ETH_per_RAI = float
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
    kind: GovernanceEventKind
    descriptor: dict


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
class UserActionParams():
    liquidation_ratio: Percentage
    debt_ceiling: RAI
    uniswap_fee: Percentage
    consider_liquidation_ratio: bool
    intensity: Percentage



@dataclass(frozen=True)
class TokenState():
    rai_reserve: RAI
    eth_reserve: ETH
    rai_debt: RAI
    eth_locked: ETH

    def __sub__(self, x):
        return TokenState(self.rai_reserve - x.rai_reserve,
                            self.eth_reserve - x.eth_reserve,
                            self.rai_debt - x.rai_debt,
                            self.eth_locked - x.eth_locked)
   

    def __add__(self, x):
        return TokenState(self.rai_reserve + x.rai_reserve,
                            self.eth_reserve + x.eth_reserve,
                            self.rai_debt + x.rai_debt,
                            self.eth_locked + x.eth_locked)


    def __mul__(self, x):
        return TokenState(self.rai_reserve * x,
                            self.eth_reserve * x,
                            self.rai_debt * x,
                            self.eth_locked * x)



DeltaTokenState = TokenState    


@dataclass(frozen=True)
class TransformedTokenState():
    # (delta_rai / debt_ceiling), or 'alpha'
    rai_debt_scaled: Percentage
    # (delta_liq_surplus / total_liq_surplus), or 'beta'
    liquidation_surplus: Percentage
    # 'gamma'
    rai_reserve_scaled: Percentage
    # 'delta'
    eth_reserve_scaled: Percentage

    def __sub__(self, x):
        return TransformedTokenState(self.rai_debt_scaled - x.rai_debt_scaled,
                                        self.liquidation_surplus - x.liquidation_surplus,
                                        self.rai_reserve_scaled - x.rai_reserve_scaled,
                                        self.eth_reserve_scaled - x.eth_reserve_scaled)



@dataclass(frozen=True)
class BacktestingData():
    token_states: dict[Timestep, TokenState]
    exogenous_data: dict[Timestep, dict[str, float]]
    heights: dict[Timestep, Height]
    pid_states: dict[Timestep, ControllerState]

@dataclass(frozen=True)
class OptimalAction():
    borrow: RAI
    repay: ETH


@dataclass(frozen=True)
class ActionState():
    token_state: TokenState
    pid_state: ControllerState
    market_price: USD_per_RAI
    eth_price: USD_per_ETH


@dataclass(frozen=True)
class PIBoundParams():
    lower_bound: float
    upper_bound: float
    default_redemption_rate: Percentage
    negative_rate_limit: Percentage

def coordinate_transform(delta_state: TokenState,
                         global_state: TokenState,
                         controller_state: ControllerState,
                         params: UserActionParams,
                         eth_price: float) -> TransformedTokenState:
    alpha = delta_state.rai_debt / params.debt_ceiling

    liquidation_price = params.liquidation_ratio
    liquidation_price *= (controller_state.redemption_price / eth_price)

    global_liquidation_surplus = liquidation_price * global_state.rai_debt
    global_liquidation_surplus -= global_state.eth_locked

    delta_liquidation_surplus = liquidation_price * delta_state.rai_debt
    delta_liquidation_surplus -= delta_state.eth_locked

    beta = delta_liquidation_surplus / global_liquidation_surplus

    gamma = delta_state.rai_reserve / global_state.rai_reserve
    delta = delta_state.eth_reserve / global_state.eth_reserve

    return TransformedTokenState(alpha,
                                 beta,
                                 gamma,
                                 delta)


def reverse_coordinate_transform(transformed_state: TransformedTokenState,
                                 global_state: TokenState,
                                 controller_state: ControllerState,
                                 params: UserActionParams,
                                 eth_price: float) -> TokenState:
    d = transformed_state.rai_debt_scaled * params.debt_ceiling

    # Liquidation Price
    l_p = params.liquidation_ratio
    l_p *= (controller_state.redemption_price / eth_price)
    beta = transformed_state.liquidation_surplus
    q = l_p * (d - beta * global_state.rai_debt)
    q += beta * global_state.eth_locked

    r = transformed_state.rai_reserve_scaled * global_state.rai_reserve
    z = transformed_state.eth_reserve_scaled * global_state.eth_reserve
    return TokenState(r, z, d, q)


def transformed_token_states_to_numpy(token_states: list[TransformedTokenState]):
    return pd.DataFrame(token_states).values
