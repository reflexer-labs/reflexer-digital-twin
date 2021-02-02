import scipy.stats as sts
import pandas as pd
import math
from .utils import approx_greater_equal_zero, assert_log
from .uniswap import get_output_price, get_input_price

import logging

############################################################################################################################################


def p_resolve_eth_price(params, substep, state_history, state):
    eth_price = params["eth_price"](state["timestep"])
    delta_eth_price = eth_price - state_history[-1][-1]["eth_price"]

    return {"delta_eth_price": delta_eth_price}


def s_update_eth_price(params, substep, state_history, state, policy_input):
    eth_price = state["eth_price"]
    delta_eth_price = policy_input["delta_eth_price"]

    return "eth_price", eth_price + delta_eth_price


def s_update_eth_return(params, substep, state_history, state, policy_input):
    eth_price = state["eth_price"]
    delta_eth_price = policy_input["delta_eth_price"]

    return "eth_return", delta_eth_price / eth_price


def s_update_eth_gross_return(params, substep, state_history, state, policy_input):
    eth_price = state["eth_price"]
    eth_gross_return = eth_price / state_history[-1][-1]["eth_price"]

    return "eth_gross_return", eth_gross_return


def s_update_stability_fee(params, substep, state_history, state, policy_input):
    stability_fee = params["stability_fee"](state["timestep"])
    return "stability_fee", stability_fee


############################################################################################################################################


def is_cdp_above_liquidation_ratio(cdp, eth_price, target_price, liquidation_ratio):
    locked = cdp["locked"]
    freed = cdp["freed"]
    drawn = cdp["drawn"]
    wiped = cdp["wiped"]
    v_bitten = cdp["v_bitten"]
    u_bitten = cdp["u_bitten"]

    # ETH * USD/ETH >= RAI * USD/RAI * unitless
    return (locked - freed - v_bitten) * eth_price >= (
        drawn - wiped - u_bitten
    ) * target_price * liquidation_ratio


def is_cdp_at_liquidation_ratio(cdp, eth_price, target_price, liquidation_ratio):
    locked = cdp["locked"]
    freed = cdp["freed"]
    drawn = cdp["drawn"]
    wiped = cdp["wiped"]
    v_bitten = cdp["v_bitten"]
    u_bitten = cdp["u_bitten"]

    # ETH * USD/ETH >= RAI * USD/RAI * unitless
    return (locked - freed - v_bitten) * eth_price == (
        drawn - wiped - u_bitten
    ) * target_price * liquidation_ratio


def wipe_to_liquidation_ratio(
    cdp, eth_price, target_price, liquidation_ratio, _raise=False
):
    locked = cdp["locked"]
    freed = cdp["freed"]
    drawn = cdp["drawn"]
    wiped = cdp["wiped"]
    v_bitten = cdp["v_bitten"]
    u_bitten = cdp["u_bitten"]

    # RAI - (USD/ETH) * ETH / (unitless * USD/RAI) -> RAI
    wipe = (drawn - wiped - u_bitten) - (locked - freed - v_bitten) * eth_price / (
        liquidation_ratio * target_price
    )
    assert_log(
        approx_greater_equal_zero(wipe, abs_tol=1e-3),
        f"wipe: {locals()}",
        _raise=_raise,
    )
    wipe = max(wipe, 0)

    if drawn <= wiped + wipe + u_bitten:
        wipe = 0

    return wipe


def draw_to_liquidation_ratio(
    cdp, eth_price, target_price, liquidation_ratio, _raise=False
):
    locked = cdp["locked"]
    freed = cdp["freed"]
    drawn = cdp["drawn"]
    wiped = cdp["wiped"]
    v_bitten = cdp["v_bitten"]
    u_bitten = cdp["u_bitten"]

    # (USD/ETH) * ETH / (USD/RAI * unitless) - RAI
    draw = (locked - freed - v_bitten) * eth_price / (
        target_price * liquidation_ratio
    ) - (drawn - wiped - u_bitten)
    assert_log(
        approx_greater_equal_zero(draw, abs_tol=1e-3), f"draw: {draw}", _raise=_raise
    )
    draw = max(draw, 0)

    return draw


def lock_to_liquidation_ratio(
    cdp, eth_price, target_price, liquidation_ratio, _raise=False
):
    locked = cdp["locked"]
    freed = cdp["freed"]
    drawn = cdp["drawn"]
    wiped = cdp["wiped"]
    v_bitten = cdp["v_bitten"]
    u_bitten = cdp["u_bitten"]

    # (USD/RAI * RAI * unitless - ETH * USD/ETH) / USD/ETH -> ETH
    lock = (
        (drawn - wiped - u_bitten) * target_price * liquidation_ratio
        - (locked - freed - v_bitten) * eth_price
    ) / eth_price
    assert_log(
        approx_greater_equal_zero(lock, abs_tol=1e-3), f"lock: {lock}", _raise=_raise
    )
    lock = max(lock, 0)

    return lock


def free_to_liquidation_ratio(
    cdp, eth_price, target_price, liquidation_ratio, _raise=False
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
        - liquidation_ratio * (drawn - wiped - u_bitten) * target_price
    ) / eth_price
    assert_log(
        approx_greater_equal_zero(free, abs_tol=1e-3), f"free: {free}", _raise=_raise
    )
    free = max(free, 0)

    return free


def open_cdp_lock(lock, eth_price, target_price, liquidation_ratio):
    # ETH * USD/ETH / (USD/RAI * unitless) -> RAI
    draw = lock * eth_price / (target_price * liquidation_ratio)
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


def open_cdp_draw(draw, eth_price, target_price, liquidation_ratio):
    # (RAI * USD/RAI * unitless) / (USD/ETH) -> ETH
    lock = (draw * target_price * liquidation_ratio) / eth_price
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


def p_rebalance_cdps(params, substep, state_history, state):
    cdps = state["cdps"]

    eth_price = state["eth_price"]
    target_price = state["target_price"]
    liquidation_ratio = params["liquidation_ratio"]
    liquidation_buffer = params["liquidation_buffer"]
    
    RAI_balance = state['RAI_balance']
    ETH_balance = state['ETH_balance']
    uniswap_fee = params['uniswap_fee']

    RAI_delta = 0
    ETH_delta = 0
    UNI_delta = 0

    for index, cdp in cdps.query("open == 1").iterrows():
        if cdp['arbitrage'] == 1:
            liquidation_buffer = 1.0
        
        cdp_above_liquidation_buffer = is_cdp_above_liquidation_ratio(
            cdp, eth_price, target_price, liquidation_ratio * liquidation_buffer
        )

        if not cdp_above_liquidation_buffer:
            # Wipe debt, using RAI from Uniswap
            wiped = cdps.at[index, "wiped"]
            wipe = wipe_to_liquidation_ratio(
                cdp,
                eth_price,
                target_price,
                liquidation_ratio * liquidation_buffer,
                params["raise_on_assert"],
            )
            # Exchange ETH for RAI
            ETH_delta, _ = get_output_price(wipe, ETH_balance, RAI_balance, uniswap_fee)
            assert ETH_delta >= 0, ETH_delta
            assert ETH_delta <= ETH_balance, ETH_delta
            RAI_delta = -wipe
            assert RAI_delta <= 0, RAI_delta
            cdps.at[index, "wiped"] = wiped + wipe
        else:
            # Draw debt, exchanging RAI for ETH in Uniswap
            drawn = cdps.at[index, "drawn"]
            draw = draw_to_liquidation_ratio(
                cdp,
                eth_price,
                target_price,
                liquidation_ratio * liquidation_buffer,
                params["raise_on_assert"],
            )
            # Exchange RAI for ETH
            _, ETH_delta = get_input_price(draw, RAI_balance, ETH_balance, uniswap_fee)
            assert ETH_delta <= 0, ETH_delta
            RAI_delta = draw
            assert RAI_delta >= 0, RAI_delta
            cdps.at[index, "drawn"] = drawn + draw

    open_cdps = len(cdps.query("open == 1"))
    closed_cdps = len(cdps.query("open == 0"))
    logging.debug(
        f"p_rebalance_cdps() ~ Number of open CDPs: {open_cdps}; Number of closed CDPs: {closed_cdps}"
    )

    uniswap_state_delta = {
        'RAI_delta': RAI_delta,
        'ETH_delta': ETH_delta,
        'UNI_delta': UNI_delta,
    }

    return {"cdps": cdps, **uniswap_state_delta}


def p_liquidate_cdps(params, substep, state_history, state):
    eth_price = state["eth_price"]
    target_price = state["target_price"]
    liquidation_penalty = params["liquidation_penalty"]
    liquidation_ratio = params["liquidation_ratio"]

    cdps = state["cdps"]
    cdps_copy = cdps.copy()
    liquidated_cdps = pd.DataFrame()
    if len(cdps) > 0:
        try:
            # The aggregate arbitrage CDP is assumed to never be liquidated
            liquidated_cdps = cdps.query("open == 1 and arbitrage == 0").query(
                f"(locked - freed - v_bitten) * {eth_price} < (drawn - wiped - u_bitten) * {target_price} * {liquidation_ratio}"
            )
        except:
            print(state)
            raise

    for index, cdp in liquidated_cdps.iterrows():
        locked = cdps.at[index, "locked"]
        freed = cdps.at[index, "freed"]
        drawn = cdps.at[index, "drawn"]
        wiped = cdps.at[index, "wiped"]
        dripped = cdps.at[index, "dripped"]
        v_bitten = cdps.at[index, "v_bitten"]
        u_bitten = cdps.at[index, "u_bitten"]
        w_bitten = cdps.at[index, "w_bitten"]

        assert_log(locked >= 0, locked, params["raise_on_assert"])
        assert_log(freed >= 0, freed, params["raise_on_assert"])
        assert_log(drawn >= 0, drawn, params["raise_on_assert"])
        assert_log(wiped >= 0, wiped, params["raise_on_assert"])
        assert_log(dripped >= 0, dripped, params["raise_on_assert"])
        assert_log(v_bitten >= 0, v_bitten, params["raise_on_assert"])
        assert_log(u_bitten >= 0, u_bitten, params["raise_on_assert"])
        assert_log(w_bitten >= 0, w_bitten, params["raise_on_assert"])

        try:
            v_bite = (
                (drawn - wiped - u_bitten) * target_price * (1 + liquidation_penalty)
            ) / eth_price
            assert v_bite >= 0, f"{v_bite} !>= 0 ~ {state}"
            assert v_bite <= (
                locked - freed - v_bitten
            ), f"Liquidation short of collateral: {v_bite} !<= {locked - freed - v_bitten}"
            free = locked - freed - v_bitten - v_bite
            assert free >= 0, f"{free} !>= {0}"
            assert (
                locked >= freed + free + v_bitten + v_bite
            ), f"locked eq check: {(locked, freed, free, v_bitten, v_bite)}"
            w_bite = dripped
            assert w_bite >= 0, f"w_bite: {w_bite}"
            u_bite = drawn - wiped - u_bitten
            assert u_bite >= 0, f"u_bite: {u_bite}"
            assert (
                u_bite <= drawn - wiped - u_bitten
            ), f"Liquidation invalid u_bite: {u_bite} !<= {drawn - wiped - u_bitten}"
        except AssertionError as err:
            logging.warning(err)
            v_bite = locked - freed - v_bitten
            u_bite = drawn - wiped - u_bitten
            free = 0
            w_bite = dripped

        cdps.at[index, "v_bitten"] = v_bitten + v_bite
        cdps.at[index, "freed"] = freed + free
        cdps.at[index, "u_bitten"] = u_bitten + u_bite
        cdps.at[index, "w_bitten"] = w_bitten + w_bite
        cdps.at[index, "open"] = 0

    v_2 = cdps["freed"].sum() - cdps_copy["freed"].sum()
    v_3 = cdps["v_bitten"].sum() - cdps_copy["v_bitten"].sum()
    u_3 = cdps["u_bitten"].sum() - cdps_copy["u_bitten"].sum()
    w_3 = cdps["w_bitten"].sum() - cdps_copy["w_bitten"].sum()

    assert_log(v_2 >= 0, v_2, params["raise_on_assert"])
    assert_log(v_3 >= 0, v_3, params["raise_on_assert"])
    assert_log(u_3 >= 0, u_3, params["raise_on_assert"])
    assert_log(w_3 >= 0, w_3, params["raise_on_assert"])

    # try:
    #     cdps = cdps.drop(liquidated_cdps.index)
    # except KeyError:
    #     print('Failed to drop CDPs')
    #     raise

    logging.debug(
        f"{len(liquidated_cdps)} CDPs liquidated with v_2 {v_2} v_3 {v_3} u_3 {u_3} w_3 {w_3}"
    )

    return {"cdps": cdps}


############################################################################################################################################


def s_store_cdps(params, substep, state_history, state, policy_input):
    return "cdps", policy_input["cdps"]


############################################################################################################################################
"""
Aggregate the state values from CDP state
"""


def get_cdps_state_change(state, state_history, key):
    cdps = state["cdps"]
    previous_cdps = state_history[-1][-1]["cdps"]
    return cdps[key].sum() - previous_cdps[key].sum()


def s_aggregate_w_1(params, substep, state_history, state, policy_input):
    return "w_1", get_cdps_state_change(state, state_history, "dripped")


def s_aggregate_w_2(params, substep, state_history, state, policy_input):
    return "w_2", get_cdps_state_change(state, state_history, "w_wiped")


def s_aggregate_w_3(params, substep, state_history, state, policy_input):
    return "w_3", get_cdps_state_change(state, state_history, "w_bitten")


############################################################################################################################################

def s_update_eth_collateral(params, substep, state_history, state, policy_input):
    eth_locked = state["eth_locked"]
    eth_freed = state["eth_freed"]
    eth_bitten = state["eth_bitten"]

    eth_collateral = eth_locked - eth_freed - eth_bitten
    event = (
        f"ETH collateral < 0: {eth_collateral} ~ {(eth_locked, eth_freed, eth_bitten)}"
    )
    if not assert_log(
        approx_greater_equal_zero(eth_collateral, 1e-2),
        event,
        params["raise_on_assert"],
    ):
        eth_collateral = 0

    return "eth_collateral", eth_collateral


def s_update_principal_debt(params, substep, state_history, state, policy_input):
    rai_drawn = state["rai_drawn"]
    rai_wiped = state["rai_wiped"]
    rai_bitten = state["rai_bitten"]

    principal_debt = rai_drawn - rai_wiped - rai_bitten

    event = (
        f"Principal debt < 0: {principal_debt} ~ {(rai_drawn, rai_wiped, rai_bitten)}"
    )
    if not assert_log(
        approx_greater_equal_zero(principal_debt, 1e-2),
        event,
        params["raise_on_assert"],
    ):
        principal_debt = 0

    return "principal_debt", principal_debt


def s_update_eth_locked(params, substep, state_history, state, policy_input):
    return "eth_locked", state['cdps']["locked"].sum()


def s_update_eth_freed(params, substep, state_history, state, policy_input):
    return "eth_freed", state['cdps']["freed"].sum()


def s_update_eth_bitten(params, substep, state_history, state, policy_input):
    return "eth_bitten", state['cdps']["v_bitten"].sum()


def s_update_rai_drawn(params, substep, state_history, state, policy_input):
    return "rai_drawn", state['cdps']["drawn"].sum()


def s_update_rai_wiped(params, substep, state_history, state, policy_input):
    return "rai_wiped", state['cdps']["wiped"].sum()


def s_update_rai_bitten(params, substep, state_history, state, policy_input):
    return "rai_bitten", state['cdps']["u_bitten"].sum()


def s_update_system_revenue(params, substep, state_history, state, policy_input):
    system_revenue = state["system_revenue"]
    w_2 = state["w_2"]
    return "system_revenue", system_revenue + w_2


def calculate_accrued_interest(
    stability_fee, target_rate, timedelta, debt, accrued_interest
):
    return (((1 + stability_fee)) ** timedelta - 1) * (debt + accrued_interest)


def s_update_accrued_interest(params, substep, state_history, state, policy_input):
    previous_accrued_interest = state["accrued_interest"]
    principal_debt = state["principal_debt"]

    stability_fee = state["stability_fee"]
    target_rate = state["target_rate"]
    timedelta = state["timedelta"]

    accrued_interest = calculate_accrued_interest(
        stability_fee, target_rate, timedelta, principal_debt, previous_accrued_interest
    )
    return "accrued_interest", previous_accrued_interest + accrued_interest


def s_update_interest_bitten(params, substep, state_history, state, policy_input):
    previous_accrued_interest = state["accrued_interest"]
    w_3 = state["w_3"]
    return "accrued_interest", previous_accrued_interest - w_3


def s_update_cdp_interest(params, substep, state_history, state, policy_input):
    cdps = state["cdps"]
    stability_fee = state["stability_fee"]
    target_rate = state["target_rate"]
    timedelta = state["timedelta"]

    def resolve_cdp_interest(cdp):
        if cdp["open"]:
            principal_debt = cdp["drawn"]
            previous_accrued_interest = cdp["dripped"]
            cdp["dripped"] = calculate_accrued_interest(
                stability_fee,
                target_rate,
                timedelta,
                principal_debt,
                previous_accrued_interest,
            )
        return cdp

    cdps = cdps.apply(resolve_cdp_interest, axis=1)

    return "cdps", cdps


def s_update_cdp_metrics(params, substep, state_history, state, policy_input):
    cdps = state["cdps"]
    cdp_metrics = {
        "cdp_count": len(cdps),
        "open_cdp_count": len(cdps.query("open == 1")),
        "closed_cdp_count": len(cdps.query("open == 0")),
        "mean_cdp_collateral": pd.eval(
            "cdp_collateral = cdps.locked - cdps.freed - cdps.v_bitten", target=cdps
        )["cdp_collateral"].mean(),
        "median_cdp_collateral": pd.eval(
            "cdp_collateral = cdps.locked - cdps.freed - cdps.v_bitten", target=cdps
        )["cdp_collateral"].median(),
    }
    return "cdp_metrics", cdp_metrics
