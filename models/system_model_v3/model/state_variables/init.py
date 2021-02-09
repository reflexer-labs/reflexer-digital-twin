from models.system_model_v3.model.state_variables.liquidity import cdps, eth_collateral, principal_debt, uniswap_rai_balance, uniswap_eth_balance
from models.system_model_v3.model.state_variables.system import stability_fee, target_price
from models.system_model_v3.model.state_variables.historical_state import eth_price
from models.system_model_v3.model.parts.uniswap_oracle import UniswapOracle

import datetime as dt


# NB: These initial states may be overriden in the relevant notebook or experiment process
state_variables = {
    # Metadata / metrics
    'cdp_metrics': {},
    'optimal_values': {},
    'sim_metrics': {},
    
    # Time states
    'timedelta': 0, # seconds
    'cumulative_time': 0, # seconds
    'timestamp': dt.datetime.strptime('2017-01-01', '%Y-%m-%d'), # type: datetime; start time
    'blockheight': 0, # block offset (init 0 simplicity)
    
    # Exogenous states
    'eth_price': eth_price, # unit: dollars; updated from historical data as exogenous parameter
    'liquidity_demand': 1,
    'liquidity_demand_mean': 1, # net transfer in or out of RAI tokens in the ETH-RAI pool
    
    # CDP states
    'cdps': cdps, # A dataframe of CDPs (both open and closed)
    # ETH collateral states
    'eth_collateral': eth_collateral, # "Q"; total ETH collateral in the CDP system i.e. locked - freed - bitten
    'eth_locked': eth_collateral, # total ETH locked into CDPs
    'eth_freed': 0, # total ETH freed from CDPs
    'eth_bitten': 0, # total ETH bitten/liquidated from CDPs
    
    # Principal debt states
    'principal_debt': principal_debt, # "D_1"; the total debt in the CDP system i.e. drawn - wiped - bitten
    'rai_drawn': principal_debt, # total RAI debt minted from CDPs
    'rai_wiped': 0, # total RAI debt wiped/burned from CDPs in repayment
    'rai_bitten': 0, # total RAI liquidated from CDPs
    
    # Accrued interest states
    'accrued_interest': 0, # "D_2"; the total interest accrued in the system i.e. current D_2 + w_1 - w_2 - w_3
    'interest_dripped': 0, # cumulative w_1 interest collected
    'interest_wiped': 0, # cumulative w_2, interest repaid - in practice acrues to MKR holders, because interest is actually acrued by burning MKR
    'interest_bitten': 0, # cumulative w_3
    'w_1': 0, # discrete "drip" event, in RAI
    'w_2': 0, # discrete "shut"/"wipe" event, in RAI
    'w_3': 0, # discrete "bite" event, in RAI
    'system_revenue': 0, # "R"; value accrued by protocol token holders as result of contracting supply
    
    # System states
    'stability_fee': stability_fee, # interest rate used to calculate the accrued interest; per second interest rate (1.5% per month)
    'market_price': target_price, # unit: dollars; the secondary market clearing price
    'market_price_twap': 0,
    'target_price': target_price, # unit: dollars; equivalent to redemption price
    'target_rate': 0 / (30 * 24 * 3600), # per second interest rate (X% per month), updated by controller
    
    # APT model states
    'eth_return': 0,
    'eth_gross_return': 0,
    'expected_market_price': target_price, # root of non-arbitrage condition
    'expected_debt_price': target_price, # predicted "debt" price, the intrinsic value of RAI according to the debt market activity and state

    # Controller states
    'error_star': 0, # price units
    'error_star_integral': 0, # price units x seconds
    
    # Uniswap states
    'market_slippage': 0,
    'RAI_balance': uniswap_rai_balance,
    'ETH_balance': uniswap_eth_balance,
    'UNI_supply': uniswap_rai_balance,
    'uniswap_oracle': UniswapOracle(
        window_size=15*3600, # 15 hours
        max_window_size=21*3600, # 21 hours
        granularity=5
    ),
}
