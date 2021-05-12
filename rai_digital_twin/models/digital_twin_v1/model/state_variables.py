import pandas as pd
from cadCAD_tools.types import InitialValue
from rai_digital_twin.types import Seconds, Height, USD_per_ETH, CDP
from rai_digital_twin.types import ETH, RAI, Percentage
from rai_digital_twin.types import USD_per_RAI, USD_Seconds_per_RAI

liquidation_ratio = 1.45
liquidation_buffer = 2

INITIAL_ETH_PRICE: USD_per_ETH = 5.0
INITIAL_REDEMPTION_PRICE: USD_per_RAI = 4.9
INITIAL_REDEMPTION_RATE: Percentage = 0.2

INITIAL_UNISWAP_ETH_RESERVE: ETH = 100
INITIAL_UNISWAP_RAI_RESERVE: RAI = 100
INITIAL_LOCKED: ETH = 100
INITIAL_DRAWN: RAI = 200

INITIAL_P_ERROR: USD_per_RAI = 0.0
INITIAL_I_ERROR: USD_Seconds_per_RAI = 0.0
INITIAL_STABILITY_FEE: Percentage = 0.03
INITIAL_MARKET_PRICE: USD_per_RAI = 5.1

aggregate_cdp = CDP(open=1,
                    time=0,
                    locked=INITIAL_LOCKED,
                    drawn=INITIAL_DRAWN,
                    wiped=0.0,
                    freed=0.0,
                    w_wiped=0.0,
                    dripped=0.0,
                    v_bitten=0.0,
                    u_bitten=0.0,
                    w_bitten=0.0)

cdp_list = [aggregate_cdp]
cdps = pd.DataFrame(cdp_list)

eth_collateral: ETH = cdps["locked"].sum()
principal_debt: ETH = cdps["drawn"].sum()


# NB: These initial states may be overriden in the relevant notebook or experiment process
state_variables: dict[str, InitialValue] = {

    # #####
    # Time states
    'timedelta': InitialValue(0, Seconds),
    'cumulative_time': InitialValue(0, Seconds),
    'blockheight': InitialValue(0, Height),

    # Exogenous states
    'eth_price': InitialValue(INITIAL_ETH_PRICE, USD_per_ETH),

    # #####
    # ## Debt Market Variables ##
    # CDP states
    'cdps': InitialValue(cdps, list[CDP]),

    # ___
    # ## ETH collateral states ##
    # Total ETH collateral in the CDP system i.e. 
    # Q(t + 1) = Q + v_1 - v_2 - v_3
    # v_1 = V_1(t + 1) - V(t), and so on.
    'eth_collateral': InitialValue(eth_collateral, ETH), # Q term
    'eth_locked': InitialValue(eth_collateral, ETH),  #* Total ETH locked. V_1(t)
    'eth_freed': InitialValue(0.0, ETH), #* Total ETH freed. V_2(t)
    'eth_bitten': InitialValue(0.0, ETH),   #* Total ETH bitten. V(_3)

    # ___
    # ## Principal debt states ##
    # "D_1"; the total debt in the CDP system i.e.
    # D_1(t + 1) =  D_1(t) + u_1 - u_2 - u_3
    # u_1 = U_1(t + 1) - U_1(t - 1), and so on

    # Used for computing interest
    'principal_debt': InitialValue(principal_debt, RAI), # D_1(t)

    # Those states are used solely for computing the principal_debt
    'rai_drawn': InitialValue(principal_debt, RAI),  # U_1(t)
    'rai_wiped': InitialValue(0, RAI), # U_2(t)
    'rai_bitten': InitialValue(0, RAI),  # U_3(t)

    # ___
    # ## Accrued interest states ##
    # "D_2"; the total interest accrued in the system 
    # i.e. D_2(t + 1) = D_2(t) + w_1 - w_2 - w_3
    'accrued_interest': InitialValue(0, RAI), # D_2(t)
    'interest_bitten': InitialValue(0, RAI),  # cumulative bite_in_rai
    'drip_in_rai': InitialValue(0, RAI), # w_1
    'wipe_in_rai': InitialValue(0, RAI), # w_2, used for system revenue 
    'bite_in_rai': InitialValue(0, RAI),  # w_3, used for interest bitten
    # "R"; value accrued by protocol token holders as result of contracting supply
    'system_revenue': InitialValue(0, RAI),  # Possible Validation Metric

    # #####
    # System states
    # interest rate used to calculate the accrued interest; per second interest rate (1.5% per month)
    'stability_fee': InitialValue(INITIAL_STABILITY_FEE, Percentage),
    'market_price_twap': InitialValue(INITIAL_MARKET_PRICE, USD_per_RAI),
    # unit: dollars; equivalent to redemption price
    'redemption_price': InitialValue(INITIAL_REDEMPTION_PRICE, USD_per_RAI),
    # per second interest rate (X% per month), updated by controller
    'redemption_rate': InitialValue(INITIAL_REDEMPTION_RATE, Percentage),

    # Controller states
    'error_star': InitialValue(INITIAL_P_ERROR, USD_per_RAI),  # price units
    'error_star_integral': InitialValue(INITIAL_I_ERROR, USD_Seconds_per_RAI),  # price units x seconds

    # Uniswap states
    'market_slippage': InitialValue(0.0, Percentage),
    'RAI_balance': InitialValue(INITIAL_UNISWAP_RAI_RESERVE, RAI),
    'ETH_balance': InitialValue(INITIAL_UNISWAP_ETH_RESERVE, ETH)
}

state_variables = {k: v.value
                   for k, v
                   in state_variables.items()}
