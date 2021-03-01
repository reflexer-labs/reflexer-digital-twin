import math
import numpy as np
import time
import logging
import pandas as pd
import statistics

from .utils import approx_greater_equal_zero, assert_log, approx_eq
from .debt_market import open_cdp_draw, open_cdp_lock, draw_to_liquidation_ratio, is_cdp_above_liquidation_ratio
from .uniswap import get_output_price, get_input_price
import models.system_model_v3.model.parts.failure_modes as failure


def p_resolve_expected_market_price(params, substep, state_history, state):
    '''
    The expected market price is assumed to be a response to unexpected changes in external
    factors (cf. APT Model documentation). The external factors are defined as:
    1. the price of ETH;
    2. swap events in the RAI-ETH Uniswap pool;
    3. add/remove events in the RAI-ETH Uniswap pool.
    '''

    debug = params['debug']

    p = state['market_price'] # price of RAI in USD
    interest_rate = params['interest_rate'] # interest rate / opportunity cost / time value of money

    try:
        eth_price = state_history[-1][-1]['eth_price']
    except IndexError as e:
        logging.exception(e)
        eth_price = state['eth_price']

    # Mean and Rate Parameters
    eth_price_data = [state[-1]['eth_price'] for state in state_history]
    eth_price_mean = statistics.mean(eth_price_data) # mean value from stochastic process of ETH price

    market_price_data = [state[-1]['market_price'] for state in state_history]
    market_price_mean = statistics.mean(market_price_data)

    # NOTE Convention on liquidity:
    # Liquidity here means the net transfer in or out of RAI tokens in the ETH-RAI pool,
    # in units of RAI, **not** units of weiRAI. If the liquidity realization is in units of
    # weiRAI it **must** be rescaled by 1e-18 before using this expected market price formulation
    liquidity_demand = state['liquidity_demand'] # Uniswap liquidity demand for RAI
    liquidity_demand_mean = state['liquidity_demand_mean'] # mean value from stochastic process of liquidity

    # APT Market Parameters
    beta_1 = params['beta_1'] # regression coefficient for ETH price
    beta_2 = params['beta_2'] # regression coefficient for liquidity shock

    # Expected Market Price in USD/RAI (cf. APT Model documentation)
    if params['liquidity_demand_shock'] == False:
        expected_market_price = p
    else:
        expected_market_price = p * (interest_rate + beta_1 * (eth_price_mean - eth_price * interest_rate)
                        + beta_2 * (liquidity_demand_mean - liquidity_demand * interest_rate))

    return {'expected_market_price': expected_market_price}

def s_store_expected_market_price(params, substep, state_history, state, policy_input):
    return 'expected_market_price', policy_input['expected_market_price']

def p_arbitrageur_model(params, substep, state_history, state):
    debug = params['debug']


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

    if not total_borrowed >= 0: raise failure.NegativeBalanceException(total_borrowed)
    if not total_deposited >= 0: raise failure.NegativeBalanceException(total_deposited)
    
    expensive_RAI_on_secondary_market = \
        redemption_price < ((1 - uniswap_fee) / liquidation_ratio) * market_price and expected_market_price < market_price \
        if params['arbitrageur_considers_liquidation_ratio'] \
        else redemption_price < (1 - uniswap_fee) * market_price and expected_market_price < market_price
    cheap_RAI_on_secondary_market = \
        redemption_price > (1 / ((1 - uniswap_fee) * liquidation_ratio)) * market_price and expected_market_price > market_price \
        if params['arbitrageur_considers_liquidation_ratio'] \
        else redemption_price > (1 / (1 - uniswap_fee)) * market_price and expected_market_price > market_price

    if expensive_RAI_on_secondary_market:
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
        
        if is_cdp_above_liquidation_ratio(
            aggregate_arbitrageur_cdp,
            eth_price,
            redemption_price,
            liquidation_ratio
        ):
            if q_deposit < 0:
                # if not is_cdp_above_liquidation_ratio(
                #     aggregate_arbitrageur_cdp,
                #     eth_price,
                #     redemption_price,
                #     liquidation_ratio
                # ): raise failure.LiquidationRatioException(context=aggregate_arbitrageur_cdp)

                available_to_borrow = draw_to_liquidation_ratio(aggregate_arbitrageur_cdp, eth_price, redemption_price, liquidation_ratio)
                if not available_to_borrow >= 0: raise failure.ArbitrageConditionException(f'{available_to_borrow=}')

                # Check if d_borrow is valid, add delta_d_borrow, using ETH from pocket
                if d_borrow > available_to_borrow:
                    delta_d_borrow = d_borrow - available_to_borrow
                    if not delta_d_borrow >= 0: raise failure.ArbitrageConditionException(f'{delta_d_borrow=}')
                    q_deposit = ((liquidation_ratio * redemption_price) / eth_price) * (total_borrowed + delta_d_borrow) - total_deposited
                else:
                    q_deposit = 0

            # Check positive profit condition
            profit = z - q_deposit - gas_price * (swap_gas_used + cdp_gas_used)
            if profit > 0:
                logging.debug(f"{state['timestamp']} Performing arb. CDP -> UNI for profit {profit}")

                borrowed = cdps.at[aggregate_arbitrageur_cdp_index, "drawn"]
                deposited = cdps.at[aggregate_arbitrageur_cdp_index, "locked"]

                if not d_borrow >= 0: raise failure.ArbitrageConditionException(f'{d_borrow=}')
                if not q_deposit >= 0: raise failure.ArbitrageConditionException(f'{q_deposit=}')
                
                cdps.at[aggregate_arbitrageur_cdp_index, "drawn"] = borrowed + d_borrow
                cdps.at[aggregate_arbitrageur_cdp_index, "locked"] = deposited + q_deposit

                RAI_delta = d_borrow
                if not RAI_delta >= 0: raise failure.ArbitrageConditionException(f'{RAI_delta=}')

                # Swap RAI for ETH
                _, ETH_delta = get_input_price(d_borrow, RAI_balance, ETH_balance, uniswap_fee)
                if not ETH_delta < 0: raise failure.ArbitrageConditionException(f'{ETH_delta=}')
                if not approx_eq(ETH_delta, -z, abs_tol=1e-5): raise failure.ArbitrageConditionException(f'{ETH_delta=} {-z=}')

    elif cheap_RAI_on_secondary_market:
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
           logging.warning("Arb. CDP closed!")
           raise failure.LiquidityException("Arb. CDP closed")

        # Check positive profit condition
        profit = q_withdraw - z - gas_price * (swap_gas_used + cdp_gas_used)
        if profit > 0:
            logging.debug(f"{state['timestamp']} Performing arb. UNI -> CDP for profit {profit}")

            repayed = cdps.at[aggregate_arbitrageur_cdp_index, "wiped"]
            withdrawn = cdps.at[aggregate_arbitrageur_cdp_index, "freed"]

            if not q_withdraw <= total_deposited: raise failure.ArbitrageConditionException(
                f"{d_repay=} {q_withdraw=} {_g2=} {RAI_balance=} {ETH_balance=} {total_borrowed=} {total_deposited=} {z=} {eth_price=} {redemption_price=} {market_price=}"
            )
            if not d_repay <= total_borrowed: raise failure.ArbitrageConditionException(
                f"{d_repay=} {q_withdraw=} {_g2=} {RAI_balance=} {ETH_balance=} {total_borrowed=} {total_deposited=} {z=} {eth_price=} {redemption_price=} {market_price=}"
            )
            
            if not d_repay >= 0: raise failure.ArbitrageConditionException(f'{d_repay=}')
            if not q_withdraw >= 0: raise failure.ArbitrageConditionException(f'{q_withdraw=}')
            
            cdps.at[aggregate_arbitrageur_cdp_index, "wiped"] = repayed + d_repay
            cdps.at[aggregate_arbitrageur_cdp_index, "freed"] = withdrawn + q_withdraw

            # Deposit ETH, get RAI
            ETH_delta, _ = get_output_price(d_repay, ETH_balance, RAI_balance, uniswap_fee)
            if not ETH_delta > 0: raise failure.ArbitrageConditionException(f'{ETH_delta=}')
            if not approx_eq(ETH_delta, z, abs_tol=1e-5): raise failure.ArbitrageConditionException(f'{ETH_delta=} {z=}')

            RAI_delta = -d_repay
            if not RAI_delta < 0: raise failure.ArbitrageConditionException(f'{RAI_delta=}')
    else:
        pass

    uniswap_state_delta = {
        'RAI_delta': RAI_delta,
        'ETH_delta': ETH_delta,
        'UNI_delta': UNI_delta,
    }

    if debug:
        cdp_update = validate_updated_cdp_state(cdps, cdps_copy)
    else:
        cdp_update = {"cdps": cdps, "optimal_values": {}}
    
    return {**cdp_update, **uniswap_state_delta}

def validate_updated_cdp_state(cdps, previous_cdps, raise_on_assert=True):
    u_1 = cdps["drawn"].sum() - previous_cdps["drawn"].sum()
    u_2 = cdps["wiped"].sum() - previous_cdps["wiped"].sum()
    v_1 = cdps["locked"].sum() - previous_cdps["locked"].sum()
    v_2 = cdps["freed"].sum() - previous_cdps["freed"].sum()

    if not u_1 >= 0: raise failure.InvalidCDPStateException(f'{u_1}')
    if not u_2 >= 0: raise failure.InvalidCDPStateException(f'{u_2}')
    if not v_1 >= 0: raise failure.InvalidCDPStateException(f'{v_1}')
    if not v_2 >= 0: raise failure.InvalidCDPStateException(f'{v_2}')

    if not approx_greater_equal_zero(
        cdps["drawn"].sum() - cdps["wiped"].sum() - cdps["u_bitten"].sum(),
        abs_tol=1e-2,
    ): raise failure.InvalidCDPStateException(f'{cdps["drawn"].sum()=} {cdps["wiped"].sum()=} {cdps["u_bitten"].sum()=}')

    if not approx_greater_equal_zero(
        cdps["locked"].sum() - cdps["freed"].sum() - cdps["v_bitten"].sum(),
        abs_tol=1e-2,
    ): raise failure.InvalidCDPStateException(f'{cdps["locked"].sum()=} {cdps["freed"].sum()=} {cdps["v_bitten"].sum()=}')

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
