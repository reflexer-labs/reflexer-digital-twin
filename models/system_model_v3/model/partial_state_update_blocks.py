from .parts.controllers import *
from .parts.markets import *
from .parts.debt_market import *
from .parts.time import *
from .parts.utils import *
from .parts.apt_model import *
from .parts.uniswap import *

partial_state_update_blocks = [
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
            # 'feature_vector': s_store_feature_vector,
            'optimal_values': s_store_optimal_values,
            # 'minimize_results': s_store_minimize_results,
            'RAI_balance': update_RAI_balance,
            'ETH_balance': update_ETH_balance,
            'UNI_supply': update_UNI_supply,
        }
    },
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
    #################################################################
    # {
    #     'details': '''
    #         Exogenous u,v activity: liquidate CDPs
    #     ''',
    #     'policies': {
    #         'liquidate_cdps': p_liquidate_cdps
    #     },
    #     'variables': {
    #         'events': s_collect_events,
    #         'cdps': s_store_cdps,
    #     }
    # },
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
    {
        'details': """
        This block computes the stability control action 
        """,
        'policies': {},
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
        'details': """
        Rebalance CDPs using wipes and draws 
        """,
        'policies': {
            'rebalance_cdps': p_rebalance_cdps,
        },
        'variables': {
            'cdps': s_store_cdps
        }
    },
    #################################################################
    {
        'policies': {},
        'variables': {
            'v_1': s_aggregate_v_1,
            'v_2': s_aggregate_v_2,
            'v_3': s_aggregate_v_3,
            'u_1': s_aggregate_u_1,
            'u_2': s_aggregate_u_2,
            'u_3': s_aggregate_u_3,
            'w_1': s_aggregate_w_1,
            'w_2': s_aggregate_w_2,
            'w_3': s_aggregate_w_3,
        }
    },
    # {
    #     'details': '''
    #         Resolve expected price and store in state
    #     ''',
    #     'policies': {
    #         'apt': p_resolve_expected_debt_price
    #     },
    #     'variables': {
    #         'expected_debt_price': s_store_expected_debt_price
    #     }
    # },
    {
        'policies': {},
        'variables': {
            'market_price': update_market_price
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
        }
    },
]
