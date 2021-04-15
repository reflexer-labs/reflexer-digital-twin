import models.system_model_v3.model.parts.markets as markets
import models.system_model_v3.model.parts.uniswap as uniswap
import models.system_model_v3.model.parts.init as init

from .parts.utils import s_update_sim_metrics, p_free_memory, s_collect_events
from .parts.governance import p_enable_controller

from .parts.controllers import *
from .parts.debt_market import *
from .parts.time import *
from .parts.apt_model import *


partial_state_update_blocks_unprocessed = [
    {
        'label': 'Initialization & Memory management',
        'policies': {
            'free_memory': p_free_memory,
            'random_seed': init.initialize_seed,
        },
        'variables': {
            'target_price': init.initialize_target_price,
        }
    },
    {
        'label': 'Time',
        'details': '''
            This block observes (or samples from data) the amount of time passed between events
        ''',
        'policies': {
            'time_process': resolve_time_passed
        },
        'variables': {
            'timedelta': store_timedelta,
            'timestamp': update_timestamp,
            'cumulative_time': update_cumulative_time
        }
    },
    #################################################################
    {
        'label': 'Liquidity',
        'enabled': True,
        'policies': {
            'liquidity_demand': markets.p_liquidity_demand
        },
        'variables': {
            'RAI_balance': uniswap.update_RAI_balance,
            'ETH_balance': uniswap.update_ETH_balance,
            'UNI_supply': uniswap.update_UNI_supply,
            'liquidity_demand': markets.s_liquidity_demand,
            'liquidity_demand_mean': markets.s_liquidity_demand_mean,
            'market_slippage': markets.s_slippage,
        }
    },
    {
        'label': 'Market Price',
        'policies': {
            'market_price': markets.p_market_price
        },
        'variables': {
            'market_price': markets.s_market_price,
            'market_price_twap': markets.s_market_price_twap,
            'uniswap_oracle': markets.s_uniswap_oracle
        }
    },
    {
        'label': 'Expected Market Price',
        'details': '''
            Resolve expected price and store in state
        ''',
        'policies': {
            'market': p_resolve_expected_market_price
        },
        'variables': {
            'expected_market_price': s_store_expected_market_price
        }
    },
    {
        'label': 'Arbitrageur',
        'details': """
            APT model
        """,
        'policies': {
            'arbitrage': p_arbitrageur_model
        },
        'variables': {
            'cdps': s_store_cdps,
            'optimal_values': s_store_optimal_values,
            'RAI_balance': uniswap.update_RAI_balance,
            'ETH_balance': uniswap.update_ETH_balance,
            'UNI_supply': uniswap.update_UNI_supply,
        }
    },
    #################################################################
    {
        'label': 'Aggregate states 1',
        'details': '''
            Aggregate states
        ''',
        'policies': {},
        'variables': {
            'eth_locked': s_update_eth_locked,
            'eth_freed': s_update_eth_freed,
            'eth_bitten': s_update_eth_bitten,
            'rai_drawn': s_update_rai_drawn,
            'rai_wiped': s_update_rai_wiped,
            'rai_bitten': s_update_rai_bitten,
        }
    },
    {
        'label': 'Debt Market 1',
        'details': '''
            Update debt market state
        ''',
        'policies': {},
        'variables': {
            'eth_collateral': s_update_eth_collateral,
            'principal_debt': s_update_principal_debt,
        }
    },
    #################################################################
    {
        'label': 'Liquidate CDPs',
        'enabled': False,
        'details': '''
            Exogenous u,v activity: liquidate CDPs
        ''',
        'policies': {
            'liquidate_cdps': p_liquidate_cdps
        },
        'variables': {
            'cdps': s_store_cdps,
        }
    },
    {
        'label': 'Rebalance CDPs',
        'details': """
        Rebalance CDPs using wipes and draws 
        """,
        'policies': {
            'rebalance_cdps': p_rebalance_cdps,
        },
        'variables': {
            'cdps': s_store_cdps,
            'RAI_balance': uniswap.update_RAI_balance,
            'ETH_balance': uniswap.update_ETH_balance,
            'UNI_supply': uniswap.update_UNI_supply,
        }
    },
    #################################################################
    {
        'label': 'Interest update',
        'details': '''
            Endogenous w activity
        ''',
        'policies': {},
        'variables': {
            'accrued_interest': s_update_accrued_interest,
            'cdps': s_update_cdp_interest
        }
    },
    #################################################################
    {
        'label': 'Compute error',
        'details': """
        This block computes and stores the error terms
        required to compute the various control actions
        """,
        'policies': {
            'observe': observe_errors
        },
        'variables': {
            'error_star': store_error_star,
            'error_star_integral': update_error_star_integral,
        }
    },
    {
        'label': 'Controller',
        'details': """
        This block computes the stability control action 
        """,
        'policies': {
            'governance': p_enable_controller,
        },
        'variables': {
            'target_rate': update_target_rate,
        }
    },
    {
        'label': 'Target price',
        'details': """
        This block updates the target price based on stability control action 
        """,
        'policies': {},
        'variables': {
            'target_price': update_target_price,
        }
    },
    #################################################################
    {
        'label': 'Aggregate W',
        'policies': {},
        'variables': {
            'w_1': s_aggregate_w_1,
            'w_2': s_aggregate_w_2,
            'w_3': s_aggregate_w_3,
        }
    },
    {
        'label': 'Aggregate states 2',
        'details': '''
            Aggregate states
        ''',
        'policies': {},
        'variables': {
            'eth_locked': s_update_eth_locked,
            'eth_freed': s_update_eth_freed,
            'eth_bitten': s_update_eth_bitten,
            'rai_drawn': s_update_rai_drawn,
            'rai_wiped': s_update_rai_wiped,
            'rai_bitten': s_update_rai_bitten,
            'accrued_interest': s_update_interest_bitten,
            'system_revenue': s_update_system_revenue,
        }
    },
    {
        'label': 'Debt Market 2',
        'details': '''
            Update debt market state
        ''',
        'policies': {},
        'variables': {
            'eth_collateral': s_update_eth_collateral,
            'principal_debt': s_update_principal_debt,
            'stability_fee': s_update_stability_fee,
        }
    },
    #################################################################
    {
        'label': 'ETH price',
        'details': '''
            Exogenous ETH price process
        ''',
        'policies': {
            'exogenous_eth_process': p_resolve_eth_price,
        },
        'variables': {
            'eth_price': s_update_eth_price,
            'eth_return': s_update_eth_return,
            'eth_gross_return': s_update_eth_gross_return
        }
    },
    #################################################################
    {
        'label': 'CDP metrics',
        'policies': {},
        'variables': {
            'cdp_metrics': s_update_cdp_metrics,
        }
    }
]

partial_state_update_blocks = list(filter(lambda psub: psub.get(
    'enabled', True), partial_state_update_blocks_unprocessed))
