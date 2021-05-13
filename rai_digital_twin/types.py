from dataclasses import dataclass

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


@dataclass()
class CDP():
    """
    Struct encapsulating a Collaterized Debt Position state for a single SAFE.
    """
    open: bool  # Is it active?
    time: float
    locked: ETH  # Locked collateral, V_1
    drawn: RAI  # U_1
    wiped: RAI  # U_2
    freed: ETH  # V_2
    w_wiped: RAI  # Accrued Interest wiped amount
    dripped: RAI  # Accrued interest, D_2
    v_bitten: ETH  # ETH Collateral liquidated amount, V_3
    u_bitten: RAI  # Principal Debt liquidated amount, U_3
    w_bitten: RAI  # Accrued Interest liquidated amount, W_3

    @property
    def collateral_in_eth(self) -> ETH:
        return self.locked - self.freed - self.v_bitten

    @property
    def debt_in_rai(self) -> RAI:
        return self.drawn - self.wiped - self.u_bitten

    def collateral_in_usd(self, eth_price: USD_per_ETH) -> USD:
        return self.collateral_in_eth * eth_price

    def debt_in_usd(self, redemption_price: USD_per_RAI) -> USD:
        return self.debt_in_rai * redemption_price

    def liquidation_threshold_in_usd(self,
                                     redemption_price: USD_per_RAI,
                                     liquidation_ratio: Percentage) -> USD:
        return self.debt_in_usd(redemption_price) * liquidation_ratio


    def is_above_liquidation_ratio(self,
                                   eth_price: USD_per_ETH,
                                   redemption_price: USD_per_RAI,
                                   liquidation_ratio: Percentage) -> bool:
        threshold = self.liquidation_threshold_in_usd(redemption_price,
                                                      liquidation_ratio)
        return (self.collateral_in_usd(eth_price) >= threshold)

    def net_debt(self, eth_price, redemption_price):
        return self.debt_in_usd(redemption_price) - self.collateral_in_usd(eth_price)