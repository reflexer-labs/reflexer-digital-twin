import math
import numpy as np
import time
import logging
import pandas as pd

from .utils import approx_greater_equal_zero, assert_log
from .debt_market import resolve_cdp_positions, open_cdp_draw, open_cdp_lock
from .uniswap import get_output_price, get_input_price


def p_resolve_expected_market_price(params, substep, state_history, state):
    eth_return = state['eth_return']
    eth_price_mean = params['eth_price_mean']
    market_price_mean = params['market_price_mean']
    eth_returns_mean = params['eth_returns_mean']
    p = state['market_price']
    interest_rate = params['interest_rate']
    
    try:
        eth_price = state_history[-1][-1]['eth_price']
    except IndexError as e:
        logging.warning(e)
        eth_price = state['eth_price']

    alpha_0 = params['alpha_0']
    alpha_1 = params['alpha_1']
    beta_0 = params['beta_0']
    beta_1 = params['beta_1']
    beta_2 = params['beta_2']
        
    # TODO: derive betas, or proxy based on stoch. process
    # TODO: maybe assumption, same types of price movements as historical MakerDAO DAI
    expected_market_price = (1 / alpha_1) * p * (interest_rate + beta_2 * (eth_price_mean - eth_price * interest_rate)
                                 + beta_1 * (market_price_mean - p * interest_rate) # TODO: changed to reflect stoch. process
                 ) - (alpha_0/alpha_1)
    
    logging.debug(f'expected_market_price terms: {alpha_1, p, interest_rate, beta_2, eth_price_mean, eth_price, beta_1, market_price_mean, alpha_0, expected_market_price}')

    # TODO: E_t p(t+1) in hackmd
    return {'expected_market_price': expected_market_price}

def s_store_expected_market_price(params, substep, state_history, state, policy_input):
    return 'expected_market_price', policy_input['expected_market_price']

def p_arbitrageur_model(params, substep, state_history, state):
    # TODO: possible metric - arb. profits/performance
    
    # TODO: calculate v, u for each CDP
    
    # Pass optimal values to CDP handler, and receive new initial condition from CDP handler
    # TODO: locks and draws, frees and wipes - independent
    # TODO: v, u will be deltas of CDP positions rather than aggregate, refactor

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

    total_borrowed = state['principal_debt']
    total_deposited = state['eth_collateral']

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
    
    if redemption_price < ((1 - uniswap_fee) / liquidation_ratio) * market_price and expected_market_price < market_price:
        print("Expensive RAI on Uni 1")
        '''
        Expensive RAI on Uni:
        (put ETH from pocket into additional collateral in CDP)
        draw RAI from CDP -> Uni
        ETH from Uni -> into pocket
        '''

        _g1 = g1(RAI_balance, ETH_balance, uniswap_fee, liquidation_ratio, redemption_price)
        d_borrow = min(debt_ceiling - total_borrowed, (_g1 - RAI_balance) / (2 * (1 - uniswap_fee)))
        q_deposit = ((liquidation_ratio * redemption_price) / eth_price) * (total_borrowed + d_borrow) - total_deposited
        z = (ETH_balance * d_borrow * (1 - uniswap_fee)) / (RAI_balance + 2 * d_borrow * (1 - uniswap_fee))

        # Check positive profit condition
        if z - q_deposit - gas_price * (swap_gas_used + cdp_gas_used) > 0:
            print("Expensive RAI on Uni 2")
            borrowed = cdps.at[aggregate_arbitrageur_cdp_index, "drawn"]
            deposited = cdps.at[aggregate_arbitrageur_cdp_index, "locked"]
            cdps.at[aggregate_arbitrageur_cdp_index, "drawn"] = borrowed + d_borrow
            cdps.at[aggregate_arbitrageur_cdp_index, "locked"] = deposited + q_deposit

            RAI_delta = d_borrow
            assert RAI_delta > 0
            _, ETH_delta = get_input_price(d_borrow, RAI_balance, ETH_balance, uniswap_fee)
            assert ETH_delta < 0

    elif redemption_price > (1 / ((1 - uniswap_fee) * liquidation_ratio)) * market_price and expected_market_price > market_price:
        print("Cheap RAI on Uni 1")
        '''
        Cheap RAI on Uni:
        ETH out of pocket -> Uni
        RAI from UNI -> CDP to wipe debt
        (and collect collteral ETH from CDP into pocket)
        '''
        
        _g2 = g2(RAI_balance, ETH_balance, uniswap_fee, liquidation_ratio, redemption_price)
        z = (_g2 - ETH_balance) / (2 * (1 - uniswap_fee))
        d_repay = (RAI_balance * z * (1 - uniswap_fee)) / (ETH_balance + 2 * z * (1 - uniswap_fee))
        q_withdraw = total_deposited - (liquidation_ratio * redemption_price / eth_price) * (total_borrowed - d_repay)
        
        # Check positive profit condition
        if q_withdraw - z - gas_price * (swap_gas_used + cdp_gas_used) > 0:
            print("Cheap RAI on Uni 2")
            repayed = cdps.at[aggregate_arbitrageur_cdp_index, "wiped"]
            withdrawn = cdps.at[aggregate_arbitrageur_cdp_index, "freed"]
            cdps.at[aggregate_arbitrageur_cdp_index, "wiped"] = repayed + d_repay
            cdps.at[aggregate_arbitrageur_cdp_index, "freed"] = withdrawn + q_withdraw

            ETH_delta, _ = get_output_price(d_repay, ETH_balance, RAI_balance, uniswap_fee)
            assert ETH_delta > 0
            RAI_delta = -d_repay
            assert RAI_delta < 0
    else:
        pass

    uniswap_state_delta = {
        'RAI_delta': RAI_delta,
        'ETH_delta': ETH_delta,
        'UNI_delta': UNI_delta,
    }
    
    # TODO: state update Q, D, cdp positions, actions passed to secondary market
    # locks and draws - sell
    # frees and wipes - buy
    
    return {**validate_updated_cdp_state(cdps, cdps_copy), 'optimal_values': {}, **uniswap_state_delta}

def validate_updated_cdp_state(cdps, previous_cdps, raise_on_assert=False):
    u_1 = cdps["drawn"].sum() - previous_cdps["drawn"].sum()
    u_2 = cdps["wiped"].sum() - previous_cdps["wiped"].sum()
    v_1 = cdps["locked"].sum() - previous_cdps["locked"].sum()
    v_2 = cdps["freed"].sum() - previous_cdps["freed"].sum()
    w_2 = 0

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
        "u_1": u_1,
        "u_2": u_2,
        "v_1": v_1,
        "v_2": v_2,
        "v_2 + v_3": v_2,
        "w_2": w_2,
    }

# TODO: remove
# def s_store_feature_vector(params, substep, state_history, state, policy_input):
#     return 'feature_vector', policy_input['feature_vector']

def s_store_optimal_values(params, substep, state_history, state, policy_input):
    return 'optimal_values', policy_input['optimal_values']

# def s_store_minimize_results(params, substep, state_history, state, policy_input):
#     return 'minimize_results', policy_input['minimize_results']
