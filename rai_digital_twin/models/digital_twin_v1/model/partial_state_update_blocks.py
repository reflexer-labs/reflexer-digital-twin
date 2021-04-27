from rai_digital_twin.models.digital_twin_v1.model.parts.user_action import p_user_action
import rai_digital_twin.models.digital_twin_v1.model.parts.markets as markets
import rai_digital_twin.models.digital_twin_v1.model.parts.uniswap as uniswap
import rai_digital_twin.models.digital_twin_v1.model.parts.init as init

from .parts.governance import p_governance_events

from .parts.controllers import *
from .parts.debt_market import *
from .parts.time import *


partial_state_update_blocks = [
    {
        'label': 'Initialization & Governance',
        'details': '',
        'policies': {
            'governance_events': p_governance_events

        },
        'variables': {
            'redemption_price': init.initialize_redemption_price,
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
    {
        'label': 'Market Price',
        'details': """
        Retrieves the Uniswap Market Price
        """,
        'policies': {
        },
        'variables': {
            'market_price_twap': markets.s_market_price_twap
        }
    },
    {
        'label': 'Aggregate states 1',
        'details': '''
            Aggregate states
        ''',
        'policies': {},
        'variables': {
            'eth_locked': cdp_sum_suf('eth_locked', 'locked'),
            'eth_freed': cdp_sum_suf('eth_freed', 'freed'),
            'eth_bitten': cdp_sum_suf('eth_bitten', 'v_bitten'),
            'rai_drawn': cdp_sum_suf('eth_drawn', 'drawn'),
            'rai_wiped': cdp_sum_suf('eth_wiped', 'wiped'),
            'rai_bitten': cdp_sum_suf('eth_bitten', 'u_bitten'),
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
        'label': 'Redemption Price',
        'details': """
        This block updates the redemption price based on stability control action 
        """,
        'policies': {},
        'variables': {
            'redemption_price': update_redemption_price,
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
            'eth_locked': cdp_sum_suf('eth_locked', 'locked'),
            'eth_freed': cdp_sum_suf('eth_freed', 'freed'),
            'eth_bitten': cdp_sum_suf('eth_bitten', 'v_bitten'),
            'rai_drawn': cdp_sum_suf('eth_drawn', 'drawn'),
            'rai_wiped': cdp_sum_suf('eth_wiped', 'wiped'),
            'rai_bitten': cdp_sum_suf('eth_bitten', 'u_bitten'),
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
    }, {
        'label': 'Aggregate User Action',
        'description': """
        Modify the macro system state according to the
        Data-driven Linearized Aggregated Arbitrageur Model
        Reference: https://hackmd.io/w-vfdZIMTDKwdEupeS3qxQ
        """,
        'policies': {
            'user_action': p_user_action
        },
        'variables': {
            'ETH_balance': None,
            'RAI_balance': None, 
            'cdps': None
        }
    }
]

partial_state_update_blocks = [psub
                               for psub
                               in partial_state_update_blocks
                               if psub.get('enabled, True') == True]
