import models.system_model_v3.model.parts.markets as markets
import models.system_model_v3.model.parts.uniswap as uniswap

from .parts.utils import s_update_sim_metrics, p_free_memory, s_collect_events
from .parts.governance import p_enable_controller

from .parts.controllers import *
from .parts.debt_market import *
from .parts.time import *
from .parts.apt_model import *


partial_state_update_blocks_unprocessed = [
    {
        'policies': {
            'free_memory': p_free_memory,
        },
        'variables': {}
    },
    {
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
        'policies': {
            'liquidity_demand': markets.p_liquidity_demand
        },
        'variables': {
            'RAI_balance': uniswap.update_RAI_balance,
            'ETH_balance': uniswap.update_ETH_balance,
            'UNI_supply': uniswap.update_UNI_supply,
        }
    },
    {
        'policies': {
            'market_price': markets.p_market_price
        },
        'variables': {
            'uniswap_oracle': markets.s_uniswap_oracle,
            'market_price': markets.s_market_price,
            'market_price_twap': markets.s_market_price_twap,
        }
    },
    {
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
        'policies': {},
        'variables': {
            'w_1': s_aggregate_w_1,
            'w_2': s_aggregate_w_2,
            'w_3': s_aggregate_w_3,
        }
    },
    {
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
        'policies': {},
        'variables': {
            'cdp_metrics': s_update_cdp_metrics,
            'sim_metrics': s_update_sim_metrics
        }
    },
]

partial_state_update_blocks = list(filter(lambda psub: psub.get('enabled', True), partial_state_update_blocks_unprocessed))
