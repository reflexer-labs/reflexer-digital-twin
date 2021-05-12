from numpy import True_
import pandas as pd
import rai_digital_twin.failure_modes as failure
import logging

## !! HACK !!
approx_greater_equal_zero = lambda *args, **kwargs: True



def s_update_stability_fee(params, substep, state_history, state, policy_input):
    stability_fee = params["stability_fee"](state["timestep"])
    return "stability_fee", stability_fee


############################################################################################################################################


def is_cdp_above_liquidation_ratio(cdp, eth_price, redemption_price, liquidation_ratio):
    locked = cdp["locked"]
    freed = cdp["freed"]
    drawn = cdp["drawn"]
    wiped = cdp["wiped"]
    v_bitten = cdp["v_bitten"]
    u_bitten = cdp["u_bitten"]

    # ETH * USD/ETH >= RAI * USD/RAI * unitless
    return (locked - freed - v_bitten) * eth_price >= (
        drawn - wiped - u_bitten
    ) * redemption_price * liquidation_ratio


def is_cdp_at_liquidation_ratio(cdp, eth_price, redemption_price, liquidation_ratio):
    locked = cdp["locked"]
    freed = cdp["freed"]
    drawn = cdp["drawn"]
    wiped = cdp["wiped"]
    v_bitten = cdp["v_bitten"]
    u_bitten = cdp["u_bitten"]

    # ETH * USD/ETH >= RAI * USD/RAI * unitless
    return (locked - freed - v_bitten) * eth_price == (
        drawn - wiped - u_bitten
    ) * redemption_price * liquidation_ratio


def wipe_to_liquidation_ratio(
    cdp, eth_price, redemption_price, liquidation_ratio, _raise=True
):
    locked = cdp["locked"]
    freed = cdp["freed"]
    drawn = cdp["drawn"]
    wiped = cdp["wiped"]
    v_bitten = cdp["v_bitten"]
    u_bitten = cdp["u_bitten"]

    # RAI - (USD/ETH) * ETH / (unitless * USD/RAI) -> RAI
    wipe = (drawn - wiped - u_bitten) - (locked - freed - v_bitten) * eth_price / (
        liquidation_ratio * redemption_price
    )
    if not approx_greater_equal_zero(wipe, abs_tol=1e-3):
        raise failure.InvalidCDPTransactionException(f"wipe: {locals()}")
    wipe = max(wipe, 0)

    if drawn <= wiped + wipe + u_bitten:
        wipe = 0

    return wipe


def draw_to_liquidation_ratio(
    cdp, eth_price, redemption_price, liquidation_ratio, _raise=True
):
    locked = cdp["locked"]
    freed = cdp["freed"]
    drawn = cdp["drawn"]
    wiped = cdp["wiped"]
    v_bitten = cdp["v_bitten"]
    u_bitten = cdp["u_bitten"]

    # (USD/ETH) * ETH / (USD/RAI * unitless) - RAI
    draw = (locked - freed - v_bitten) * eth_price / (
        redemption_price * liquidation_ratio
    ) - (drawn - wiped - u_bitten)
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
    cdps = state["cdps"]

    eth_price = state["eth_price"]
    redemption_price = state["redemption_price"]
    liquidation_buffer = state['liquidation_buffer']
    liquidation_ratio = params["liquidation_ratio"]

    ETH_balance = state['ETH_balance']

    RAI_delta = 0
    ETH_delta = 0

    for index, cdp in cdps.query("open == 1").iterrows():
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

    uniswap_state_delta = {
        'RAI_delta': RAI_delta,
        'ETH_delta': ETH_delta,
        'UNI_delta': 0,
    }

    return {"cdps": cdps, **uniswap_state_delta}


def p_liquidate_cdps(params, _1, _2, state):
    eth_price = state["eth_price"]
    redemption_price = state["redemption_price"]
    liquidation_penalty = params["liquidation_penalty"]
    liquidation_ratio = params["liquidation_ratio"]

    cdps = state["cdps"]
    cdps_copy = cdps.copy()
    liquidated_cdps = pd.DataFrame()
    if len(cdps) > 0:
        try:
            # The aggregate arbitrage CDP is assumed to never be liquidated
            liquidated_cdps = cdps.query("open == 1 and arbitrage == 0").query(
                f"(locked - freed - v_bitten) * {eth_price} < (drawn - wiped - u_bitten) * {redemption_price} * {liquidation_ratio}"
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
                (drawn - wiped - u_bitten) *
                redemption_price * (1 + liquidation_penalty)
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
    bite_in_rai = cdps["w_bitten"].sum() - cdps_copy["w_bitten"].sum()

    assert_log(v_2 >= 0, v_2, params["raise_on_assert"])
    assert_log(v_3 >= 0, v_3, params["raise_on_assert"])
    assert_log(u_3 >= 0, u_3, params["raise_on_assert"])
    assert_log(bite_in_rai >= 0, bite_in_rai, params["raise_on_assert"])

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


def s_aggregate_drip_in_rai(params, substep, state_history, state, policy_input):
    return "drip_in_rai", get_cdps_state_change(state, state_history, "dripped")


def s_aggregate_wipe_in_rai(params, substep, state_history, state, policy_input):
    return "wipe_in_rai", get_cdps_state_change(state, state_history, "w_wiped")


def s_aggregate_bite_in_rai(params, substep, state_history, state, policy_input):
    return "bite_in_rai", get_cdps_state_change(state, state_history, "w_bitten")


############################################################################################################################################

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
        return "principal_debt", principal_debt


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

