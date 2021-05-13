from cadCAD_tools.types import History, State, StateUpdate, VariableUpdate
import pandas as pd
import rai_digital_twin.failure_modes as failure
from rai_digital_twin.types import CDP, ETH, Percentage, RAI_per_USD, USD, USD_per_ETH, USD_per_RAI

# !! HACK !!
approx_greater_equal_zero = lambda *args, **kwargs: True


def s_update_stability_fee(params, substep, state_history, state, policy_input):
    stability_fee = params["stability_fee"](state["timestep"])
    return "stability_fee", stability_fee


def wipe_to_liquidation_ratio(
    cdp, eth_price, redemption_price, liquidation_ratio, _raise=True
):
    net_debt = cdp.net_debt(eth_price, redemption_price)
    rai_to_wipe = net_debt / liquidation_ratio
    rai_to_wipe = max(rai_to_wipe, 0)
    # Only wipe if the CDP drawn amount is higher than the
    # total wiped + bitten amount
    if cdp.drawn <= cdp.wiped + rai_to_wipe + cdp.u_bitten:
        rai_to_wipe = 0
    else:
        pass
    return rai_to_wipe


def draw_to_liquidation_ratio(
    cdp, eth_price, redemption_price, liquidation_ratio, _raise=True
):

    # (USD/ETH) * ETH / (USD/RAI * unitless) - RAI
    draw = (cdp.locked - cdp.freed - cdp.v_bitten) * eth_price / (
        redemption_price * liquidation_ratio
    ) - (cdp.drawn - cdp.wiped - cdp.u_bitten)
    if not approx_greater_equal_zero(draw, abs_tol=1e-3):
        raise failure.InvalidCDPTransactionException(f"draw: {locals()}")
    draw = max(draw, 0)

    return draw


def lock_to_liquidation_ratio(
    cdp, eth_price, redemption_price, liquidation_ratio, _raise=True
):
    locked = cdp["locked"]
    freed = cdp["freed"]
    drawn = cdp["drawn"]
    wiped = cdp["wiped"]
    v_bitten = cdp["v_bitten"]
    u_bitten = cdp["u_bitten"]

    # (USD/RAI * RAI * unitless - ETH * USD/ETH) / USD/ETH -> ETH
    lock = (
        (drawn - wiped - u_bitten) * redemption_price * liquidation_ratio
        - (locked - freed - v_bitten) * eth_price
    ) / eth_price
    if not approx_greater_equal_zero(lock, abs_tol=1e-3):
        raise failure.InvalidCDPTransactionException(f"lock: {lock}")
    lock = max(lock, 0)

    return lock


def free_to_liquidation_ratio(
    cdp, eth_price, redemption_price, liquidation_ratio, _raise=True
):
    locked = cdp["locked"]
    freed = cdp["freed"]
    drawn = cdp["drawn"]
    wiped = cdp["wiped"]
    v_bitten = cdp["v_bitten"]
    u_bitten = cdp["u_bitten"]

    # (ETH * USD/ETH - unitless * RAI * USD/RAI) / (USD/ETH) -> ETH
    free = (
        (locked - freed - v_bitten) * eth_price
        - liquidation_ratio * (drawn - wiped - u_bitten) * redemption_price
    ) / eth_price
    if not approx_greater_equal_zero(free, abs_tol=1e-3):
        raise failure.InvalidCDPTransactionException(f"free: {free}")
    free = max(free, 0)

    return free


def open_cdp_lock(lock, eth_price, redemption_price, liquidation_ratio):
    # ETH * USD/ETH / (USD/RAI * unitless) -> RAI
    draw = lock * eth_price / (redemption_price * liquidation_ratio)
    return {
        "open": 1,
        "time": 0,
        "locked": lock,
        "drawn": draw,
        "wiped": 0.0,
        "freed": 0.0,
        "w_wiped": 0.0,
        "dripped": 0.0,
        "v_bitten": 0.0,
        "u_bitten": 0.0,
        "w_bitten": 0.0,
    }


def open_cdp_draw(draw, eth_price, redemption_price, liquidation_ratio):
    # (RAI * USD/RAI * unitless) / (USD/ETH) -> ETH
    lock = (draw * redemption_price * liquidation_ratio) / eth_price
    return {
        "open": 1,
        "time": 0,
        "locked": lock,
        "drawn": draw,
        "wiped": 0.0,
        "freed": 0.0,
        "w_wiped": 0.0,
        "dripped": 0.0,
        "v_bitten": 0.0,
        "u_bitten": 0.0,
        "w_bitten": 0.0,
    }


def rebalance_cdp(params: dict,
                  cdps: pd.DataFrame,
                  eth_price: float,
                  redemption_price: float,
                  liquidation_ratio: float,
                  ETH_balance: float,
                  index: int,
                  cdp: dict,
                  ETH_delta: float,
                  liquidation_buffer: float) -> tuple:
    """

    """
    if cdp['arbitrage'] == 1:
        liquidation_buffer = 1.0
    else:
        pass

    args = (cdp,
            eth_price,
            redemption_price,
            liquidation_ratio * liquidation_buffer)
    cdp_above_liquidation_buffer = is_cdp_above_liquidation_ratio(*args)

    if not cdp_above_liquidation_buffer:
        # Wipe debt, using RAI from Uniswap
        wiped = cdps.at[index, "wiped"]
        wipe_args = (cdp,
                     eth_price,
                     redemption_price,
                     liquidation_ratio * liquidation_buffer,
                     params["raise_on_assert"])
        wipe = wipe_to_liquidation_ratio(*wipe_args)
        RAI_delta = -wipe

        if not ETH_delta >= 0:
            raise failure.InvalidSecondaryMarketDeltaException(f'{ETH_delta=}')
        elif not ETH_delta <= ETH_balance:
            raise failure.InvalidSecondaryMarketDeltaException(f'{ETH_delta=}')
        elif not RAI_delta <= 0:
            raise failure.InvalidSecondaryMarketDeltaException(f'{RAI_delta=}')
        else:
            # Wipe amount on the CDPs
            cdps.at[index, "wiped"] = wiped + wipe
    else:
        # Draw debt, exchanging RAI for ETH in Uniswap
        drawn = cdps.at[index, "drawn"]
        draw = draw_to_liquidation_ratio(
            cdp,
            eth_price,
            redemption_price,
            liquidation_ratio * liquidation_buffer,
            params["raise_on_assert"],
        )
        # Exchange RAI for ETH_, ETH_delta = get_input_price(draw, RAI_balance, ETH_balance, uniswap_fee)
        if not ETH_delta <= 0:
            raise failure.InvalidSecondaryMarketDeltaException(f'{ETH_delta=}')
        RAI_delta = draw
        if not RAI_delta >= 0:
            raise failure.InvalidSecondaryMarketDeltaException(f'{RAI_delta=}')
        cdps.at[index, "drawn"] = drawn + draw
    return RAI_delta, ETH_delta, cdps


def p_rebalance_cdps(params, _1, _2, state):
    """

    """
    # Parameters & Variables
    liquidation_ratio = params["liquidation_ratio"]
    cdps = state["cdps"]
    eth_price = state["eth_price"]
    redemption_price = state["redemption_price"]
    liquidation_buffer = state['liquidation_buffer']
    ETH_balance = state['ETH_balance']

    # ---
    (RAI_delta, ETH_delta) = (0.0, 0.0)
    open_cdps = cdps.query("open == 1")

    # Rebalance each CDP
    for index, cdp in open_cdps.iterrows():
        RAI_delta, ETH_delta, cdps = rebalance_cdp(params,
                                                   cdps,
                                                   eth_price,
                                                   redemption_price,
                                                   liquidation_ratio,
                                                   ETH_balance,
                                                   index,
                                                   cdp,
                                                   ETH_delta,
                                                   liquidation_buffer)

    # Output
    rebalancing_results = {
        'cdps': cdps,
        'RAI_delta': RAI_delta,
        'ETH_delta': ETH_delta,
        'UNI_delta': 0,
    }

    return rebalancing_results


def liquidate_cdp(cdp: CDP,
                  liquidation_penalty: Percentage,
                  rai_price_in_eth: RAI_per_USD) -> CDP:
    """
    Liquidate CDP
    """
    # Auxiliary variables
    cdp_principal_debt = cdp.drawn - cdp.wiped - cdp.u_bitten
    cdp_collateral = cdp.locked - cdp.freed - cdp.v_bitten
    bite_fraction = (1 + liquidation_penalty)

    # ETH to be bitten
    v_bite = cdp_principal_debt * rai_price_in_eth * bite_fraction

    # Liquidation action
    (v_bite, free, u_bite, w_bite) = (0.0, 0.0, 0.0, 0.0)

    # Feasibility constraints
    conditions = [0.0 <= v_bite <= cdp_collateral,
                  0.0 <= free <= cdp_collateral - v_bite,
                  0.0 <= w_bite,
                  0.0 <= u_bite, + cdp_principal_debt]

    # Bite CDP debt and free some of the ETH collateral if
    # conditions are true.
    if sum(conditions) / len(conditions) == 1.0:
        v_bite = v_bite
        free = cdp_collateral - v_bite,
        w_bite = cdp.dripped
        u_bite = cdp_principal_debt
    # Else, just bite it without freeing CDP ETH collateral
    else:
        v_bite = cdp_collateral
        free = 0.0
        u_bite = cdp_principal_debt
        w_bite = cdp.dripped

    # Update CDP state
    cdp.v_bitten = cdp.v_bitten + v_bite
    cdp.freed = cdp.freed + free
    cdp.u_bitten = cdp.u_bitten + u_bite
    cdp.w_bitten = cdp.w_bitten + w_bite
    cdp.open = 0

    # Return CDP
    return cdp


def p_liquidate_cdps(params, _1, _2, state):
    """
    CDP Liquidation Policy
    """
    # Parameters & Variables
    liquidation_penalty = params["liquidation_penalty"]
    liquidation_ratio = params["liquidation_ratio"]
    eth_price = state["eth_price"]
    redemption_price = state["redemption_price"]
    cdps = state["cdps"]
    cdps_copy = cdps.copy()

    # Auxiliary Variables
    rai_price_in_eth = redemption_price / eth_price
    liquidation_price = redemption_price * liquidation_ratio

    # Compute relevant metrics for CDP liquidation
    def f(df): return (df.locked - df.freed - df.v_bitten) * eth_price
    def g(df): return (df.drawn - df.wiped - df.u_bitten) * liquidation_price
    CDP_METRICS = {'collateral_in_rai': f,
                   'liquidation_threshold_in_rai': g}

    # Retrieve all CDPs to be liquidated
    QUERY = """open == 1 & arbitrage == 0 & collateral_in_rai < liquidation_threshold_in_rai"""

    # Retrieve data frame with CDPs to be liquidated
    liquidated_cdps = (cdps.assign(**CDP_METRICS)
                           .query(QUERY)
                       )

    # Liquidate CDPs and update the debt market state
    for index, cdp in liquidated_cdps.iterrows():
        cdp = liquidate_cdp(cdp, liquidation_penalty, rai_price_in_eth)
        cdps.iloc[index] = cdp

    # Return new CDP states
    return {"cdps": cdps}


############################################################################################################################################
"""
Aggregate the state values from CDP state
"""


def get_cdps_state_change(state: State,
                          state_history: History,
                          key: str) -> float:
    cdps = state["cdps"]
    previous_cdps = state_history[-1][-1]["cdps"]
    return cdps[key].sum() - previous_cdps[key].sum()


def cdp_state_change_metric(variable: str, cdp_attribute: str) -> StateUpdate:
    def suf(_1, _2, history, state, _5) -> VariableUpdate:
        return (variable, get_cdps_state_change(state, history, cdp_attribute))
    return suf


def s_update_eth_collateral(params, substep, state_history, state, policy_input):
    eth_locked = state["eth_locked"]
    eth_freed = state["eth_freed"]
    eth_bitten = state["eth_bitten"]

    eth_collateral = eth_locked - eth_freed - eth_bitten

    if not approx_greater_equal_zero(eth_collateral, 1e-2):
        event = f"ETH collateral < 0: {eth_collateral} ~ {(eth_locked, eth_freed, eth_bitten)}"
        raise failure.NegativeBalanceException(event)
    else:
        return ("eth_collateral", eth_collateral)


def s_update_principal_debt(params, substep, state_history, state, policy_input):
    rai_drawn = state["rai_drawn"]
    rai_wiped = state["rai_wiped"]
    rai_bitten = state["rai_bitten"]

    principal_debt = rai_drawn - rai_wiped - rai_bitten

    if not approx_greater_equal_zero(principal_debt, 1e-2):
        event = f"Principal debt < 0: {principal_debt} ~ {(rai_drawn, rai_wiped, rai_bitten)}"
        raise failure.NegativeBalanceException(event)
    else:
        return ("principal_debt", principal_debt)


def cdp_sum_suf(variable: str, cdp_column: str) -> object:
    """
    Generates a State Update Function that sums over the
    cdps state variable
    """
    def suf(params, substep, state_history, state, policy_input):
        return variable, state['cdps'][cdp_column].sum()
    return suf


def s_update_system_revenue(params, substep, state_history, state, policy_input):
    system_revenue = state["system_revenue"]
    wipe_in_rai = state["wipe_in_rai"]
    return "system_revenue", system_revenue + wipe_in_rai


def calculate_accrued_interest(
    stability_fee, redemption_rate, timedelta, debt, accrued_interest
):
    return (((1 + stability_fee)) ** timedelta - 1) * (debt + accrued_interest)


def s_update_accrued_interest(params, substep, state_history, state, policy_input):
    previous_accrued_interest = state["accrued_interest"]
    principal_debt = state["principal_debt"]

    stability_fee = state["stability_fee"]
    redemption_rate = state["redemption_rate"]
    timedelta = state["timedelta"]

    accrued_interest = calculate_accrued_interest(
        stability_fee, redemption_rate, timedelta, principal_debt, previous_accrued_interest
    )
    return "accrued_interest", previous_accrued_interest + accrued_interest


def s_update_interest_bitten(params, substep, state_history, state, policy_input):
    previous_accrued_interest = state["accrued_interest"]
    bite_in_rai = state["bite_in_rai"]
    return "accrued_interest", previous_accrued_interest - bite_in_rai


def s_update_cdp_interest(params, substep, state_history, state, policy_input):
    cdps = state["cdps"]
    stability_fee = state["stability_fee"]
    redemption_rate = state["redemption_rate"]
    timedelta = state["timedelta"]

    def resolve_cdp_interest(cdp):
        if cdp["open"]:
            principal_debt = cdp['drawn'] - cdp['wiped'] - cdp['u_bitten']
            previous_accrued_interest = cdp["dripped"]
            cdp["dripped"] = calculate_accrued_interest(
                stability_fee,
                redemption_rate,
                timedelta,
                principal_debt,
                previous_accrued_interest,
            )
        return cdp

    cdps = cdps.apply(resolve_cdp_interest, axis=1)

    return "cdps", cdps
