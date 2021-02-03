import math
import numpy as np
import time
import logging
import pandas as pd
import statistics

from .utils import approx_greater_equal_zero, assert_log, approx_eq
from .debt_market import open_cdp_draw, open_cdp_lock, draw_to_liquidation_ratio, is_cdp_above_liquidation_ratio
from .uniswap import get_output_price, get_input_price


def p_resolve_expected_market_price(params, substep, state_history, state):
    eth_return = state['eth_return']
    eth_price_mean = params['eth_price_mean']
    eth_returns_mean = params['eth_returns_mean']
    p = state['market_price']
    interest_rate = params['interest_rate']
    
    try:
        eth_price = state_history[-1][-1]['eth_price']
    except IndexError as e:
        logging.warning(e)
        eth_price = state['eth_price']

    market_price_data = [state[-1]['market_price'] for state in state_history]
    market_price_mean = statistics.mean(market_price_data)

    # eth_price_data = [state[-1]['eth_price'] for state in state_history]
    # eth_price_mean = statistics.mean(eth_price_data)

    # eth_return_data = [state[-1]['eth_return'] for state in state_history]
    # eth_returns_mean = statistics.mean(eth_return_data)

    alpha_0 = params['alpha_0']
    alpha_1 = params['alpha_1']
    beta_0 = params['beta_0']
    beta_1 = params['beta_1']
    beta_2 = params['beta_2']

    """
    TODO: changed to reflect stoch. process
    * derive betas, or proxy based on stoch. process
    * maybe assumption, same types of price movements as historical MakerDAO DAI
    """    

    expected_market_price = (1 / alpha_1) * p * (interest_rate + beta_2 * (eth_price_mean - eth_price * interest_rate)
                                 + beta_1 * (market_price_mean - p * interest_rate)
                 ) - (alpha_0/alpha_1)

    logging.debug(f'expected_market_price terms: {alpha_1, p, interest_rate, beta_2, eth_price_mean, eth_price, beta_1, market_price_mean, alpha_0, expected_market_price}')

    return {'expected_market_price': expected_market_price}

def s_store_expected_market_price(params, substep, state_history, state, policy_input):
    return 'expected_market_price', policy_input['expected_market_price']

def p_arbitrageur_model(params, substep, state_history, state):
    # TODO: possible metric - arb. profits/performance

    RAI_balance = state['RAI_balance']
    ETH_balance = state['ETH_balance']
    UNI_supply = state['UNI_supply']

    RAI_delta = 0
    ETH_delta = 0
    UNI_delta = 0

    redemption_price = state['target_price']
    expected_market_price = state['expected_market_price']
    market_price = state['market_price']
    eth_price = state['eth_price']

    uniswap_fee = params['uniswap_fee']
    liquidation_ratio = params['liquidation_ratio']
    debt_ceiling = params['debt_ceiling']

    gas_price = params['gas_price']
    swap_gas_used = params['swap_gas_used']
    cdp_gas_used = params['cdp_gas_used']

    def g1(RAI_balance, ETH_balance, uniswap_fee, liquidation_ratio, redemption_price):
        return ((eth_price * RAI_balance * ETH_balance * (1 - uniswap_fee)) / (liquidation_ratio * redemption_price)) ** 0.5

    def g2(RAI_balance, ETH_balance, uniswap_fee, liquidation_ratio, redemption_price):
        return (RAI_balance * ETH_balance * (1 - uniswap_fee) * liquidation_ratio * (redemption_price / eth_price)) ** 0.5

    cdps = state['cdps']
    cdps_copy = cdps.copy()
    aggregate_arbitrageur_cdp_index = cdps.query("arbitrage == 1").index[0]
    aggregate_arbitrageur_cdp = cdps.loc[aggregate_arbitrageur_cdp_index]

    total_borrowed = aggregate_arbitrageur_cdp['drawn'] - aggregate_arbitrageur_cdp['wiped'] - aggregate_arbitrageur_cdp['u_bitten']
    total_deposited = aggregate_arbitrageur_cdp['locked'] - aggregate_arbitrageur_cdp['freed'] - aggregate_arbitrageur_cdp['v_bitten']

    assert total_borrowed >= 0, total_borrowed
    assert total_deposited >= 0, total_deposited
    
    if redemption_price < ((1 - uniswap_fee) / liquidation_ratio) * market_price and expected_market_price < market_price:
        '''
        Expensive RAI on Uni:
        (put ETH from pocket into additional collateral in CDP)
        draw RAI from CDP -> Uni
        ETH from Uni -> into pocket
        '''

        _g1 = g1(RAI_balance, ETH_balance, uniswap_fee, liquidation_ratio, redemption_price)
        d_borrow = min(debt_ceiling - total_borrowed, (_g1 - RAI_balance) / (1 - uniswap_fee))
        q_deposit = ((liquidation_ratio * redemption_price) / eth_price) * (total_borrowed + d_borrow) - total_deposited
        z = (ETH_balance * d_borrow * (1 - uniswap_fee)) / (RAI_balance + d_borrow * (1 - uniswap_fee))

        if q_deposit < 0:
            assert is_cdp_above_liquidation_ratio(
                aggregate_arbitrageur_cdp,
                eth_price,
                redemption_price,
                liquidation_ratio
            ), aggregate_arbitrageur_cdp

            available_to_borrow = draw_to_liquidation_ratio(aggregate_arbitrageur_cdp, eth_price, redemption_price, liquidation_ratio)
            assert available_to_borrow >= 0, available_to_borrow

            # Check if d_borrow is valid, add delta_d_borrow, using ETH from pocket
            if d_borrow > available_to_borrow:
                delta_d_borrow = d_borrow - available_to_borrow
                assert delta_d_borrow >= 0
                q_deposit = ((liquidation_ratio * redemption_price) / eth_price) * (total_borrowed + delta_d_borrow) - total_deposited
            else:
                q_deposit = 0

        # Check positive profit condition
        profit = z - q_deposit - gas_price * (swap_gas_used + cdp_gas_used)
        if profit > 0:
            print(f"{state['timestamp']} Performing arb. CDP -> UNI for profit {profit}")

            borrowed = cdps.at[aggregate_arbitrageur_cdp_index, "drawn"]
            deposited = cdps.at[aggregate_arbitrageur_cdp_index, "locked"]

            assert d_borrow >= 0, d_borrow
            assert q_deposit >= 0, (q_deposit, redemption_price, eth_price, total_borrowed, d_borrow, total_deposited)
            
            cdps.at[aggregate_arbitrageur_cdp_index, "drawn"] = borrowed + d_borrow
            cdps.at[aggregate_arbitrageur_cdp_index, "locked"] = deposited + q_deposit

            RAI_delta = d_borrow
            assert RAI_delta > 0, RAI_delta

            # Swap RAI for ETH
            _, ETH_delta = get_input_price(d_borrow, RAI_balance, ETH_balance, uniswap_fee)
            assert ETH_delta < 0, ETH_delta
            assert approx_eq(ETH_delta, -z, abs_tol=1e-5), (ETH_delta, -z)

    elif redemption_price > (1 / ((1 - uniswap_fee) * liquidation_ratio)) * market_price and expected_market_price > market_price:
        '''
        Cheap RAI on Uni:
        ETH out of pocket -> Uni
        RAI from UNI -> CDP to wipe debt
        (and collect collteral ETH from CDP into pocket)
        '''
        
        _g2 = g2(RAI_balance, ETH_balance, uniswap_fee, liquidation_ratio, redemption_price)
        z = (_g2 - ETH_balance) / (1 - uniswap_fee)
        d_repay = (RAI_balance * z * (1 - uniswap_fee)) / (ETH_balance + z * (1 - uniswap_fee))
        q_withdraw = total_deposited - (liquidation_ratio * redemption_price / eth_price) * (total_borrowed - d_repay)
        
        if d_repay > total_borrowed:
           print("Arb. CDP closed!")
           logging.warning(f"{d_repay=} {q_withdraw=} {_g2=} {RAI_balance=} {ETH_balance=} {total_borrowed=} {total_deposited=} {z=} {eth_price=} {redemption_price=} {market_price=}")
           d_repay = total_borrowed
           z, _ = get_output_price(d_repay, ETH_balance, RAI_balance, uniswap_fee)
           q_withdraw = total_deposited
           cdps.at[aggregate_arbitrageur_cdp_index, "closed"] = 1

        # Check positive profit condition
        profit = q_withdraw - z - gas_price * (swap_gas_used + cdp_gas_used)
        if profit > 0:
            print(f"{state['timestamp']} Performing arb. UNI -> CDP for profit {profit}")

            repayed = cdps.at[aggregate_arbitrageur_cdp_index, "wiped"]
            withdrawn = cdps.at[aggregate_arbitrageur_cdp_index, "freed"]

            assert q_withdraw <= total_deposited, f"{d_repay=} {q_withdraw=} {_g2=} {RAI_balance=} {ETH_balance=} {total_borrowed=} {total_deposited=} {z=} {eth_price=} {redemption_price=} {market_price=}"
            assert d_repay <= total_borrowed, f"{d_repay=} {q_withdraw=} {_g2=} {RAI_balance=} {ETH_balance=} {total_borrowed=} {total_deposited=} {z=} {eth_price=} {redemption_price=} {market_price=}"
            
            assert d_repay >= 0, d_repay
            assert q_withdraw >= 0, q_withdraw
            
            cdps.at[aggregate_arbitrageur_cdp_index, "wiped"] = repayed + d_repay
            cdps.at[aggregate_arbitrageur_cdp_index, "freed"] = withdrawn + q_withdraw

            # Deposit ETH, get RAI
            ETH_delta, _ = get_output_price(d_repay, ETH_balance, RAI_balance, uniswap_fee)
            assert ETH_delta > 0, ETH_delta
            assert approx_eq(ETH_delta, z, abs_tol=1e-5), (ETH_delta, z)

            RAI_delta = -d_repay
            assert RAI_delta < 0, RAI_delta
    else:
        pass

    uniswap_state_delta = {
        'RAI_delta': RAI_delta,
        'ETH_delta': ETH_delta,
        'UNI_delta': UNI_delta,
    }
    
    return {**validate_updated_cdp_state(cdps, cdps_copy), **uniswap_state_delta}

def validate_updated_cdp_state(cdps, previous_cdps, raise_on_assert=True):
    u_1 = cdps["drawn"].sum() - previous_cdps["drawn"].sum()
    u_2 = cdps["wiped"].sum() - previous_cdps["wiped"].sum()
    v_1 = cdps["locked"].sum() - previous_cdps["locked"].sum()
    v_2 = cdps["freed"].sum() - previous_cdps["freed"].sum()

    assert_log(u_1 >= 0, u_1, raise_on_assert)
    assert_log(u_2 >= 0, u_2, raise_on_assert)
    assert_log(v_1 >= 0, v_1, raise_on_assert)
    assert_log(v_2 >= 0, v_2, raise_on_assert)

    assert_log(
        approx_greater_equal_zero(
            cdps["drawn"].sum() - cdps["wiped"].sum() - cdps["u_bitten"].sum(),
            abs_tol=1e-2,
        ),
        (cdps["drawn"].sum(), cdps["wiped"].sum(), cdps["u_bitten"].sum()),
        raise_on_assert,
    )

    assert_log(
        approx_greater_equal_zero(
            cdps["locked"].sum() - cdps["freed"].sum() - cdps["v_bitten"].sum(),
            abs_tol=1e-2,
        ),
        (cdps["locked"].sum(), cdps["freed"].sum(), cdps["v_bitten"].sum()),
        raise_on_assert,
    )

    return {
        "cdps": cdps,
        'optimal_values': {
            "u_1": u_1,
            "u_2": u_2,
            "v_1": v_1,
            "v_2": v_2,
        }
    }

def s_store_optimal_values(params, substep, state_history, state, policy_input):
    return 'optimal_values', policy_input['optimal_values']
