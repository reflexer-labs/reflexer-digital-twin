from rai_digital_twin.models.digital_twin_v1.model.parts.backtesting import p_backtesting, s_cdp_backtesting
from typing import List
from cadCAD_tools import generic_suf

# Meta stuff
from .parts.initialization import initialize_redemption_price
from .parts.time import p_resolve_time_passed
from .parts.time import s_store_timedelta, s_update_cumulative_time

# Events
from .parts.governance import p_governance_events
from .parts.user_action import p_user_action, s_CDP_action

# Exogenous Info
from .parts.markets import s_ETH_balance, s_RAI_balance, s_market_price_twap

# Controllers
from .parts.controllers import observe_errors
from .parts.controllers import store_error_star, update_error_star_integral
from .parts.controllers import update_redemption_price, update_redemption_rate

# Debt Market
from .parts.debt_market import p_liquidate_cdps, p_rebalance_cdps
from .parts.debt_market import cdp_sum_suf, s_update_eth_collateral, s_update_principal_debt
from .parts.debt_market import s_store_cdps
from .parts.debt_market import s_update_system_revenue
from .parts.debt_market import s_update_accrued_interest, s_update_cdp_interest
from .parts.debt_market import s_aggregate_drip_in_rai, s_aggregate_wipe_in_rai, s_aggregate_bite_in_rai
from .parts.debt_market import s_update_interest_bitten, s_update_stability_fee


partial_state_update_blocks: List[dict] = [
    {
        'label': 'Time',
        'details': '''
            This block observes (or samples from data) the amount of time passed between events
        ''',
        'policies': {
            'time_process': p_resolve_time_passed
        },
        'variables': {
            'timedelta': s_store_timedelta,
            'cumulative_time': s_update_cumulative_time
        }
    },
        {
        'label': 'Initialization & Governance',
        'details': '',
        'policies': {
            'governance_events': p_governance_events

        },
        'variables': {
            'redemption_price': initialize_redemption_price,
        }
    },
    {
        'label': 'Backtesting Exogenous Variables',
        'flags': {'backtesting'},
        'policies': {
            'backtesting_data': p_backtesting
        },
        'variables': {
            'eth_price': generic_suf('eth_price'),
            'market_price_twap': generic_suf('market_price_twap'),
            'RAI_balance': generic_suf('RAI_balance'),
            'ETH_balance': generic_suf('ETH_balance'),
            'cdps': s_cdp_backtesting
        }
    },
    {
        'label': 'Extrapolation Exogenous Variables',
        'flags': {'extrapolation'},
        'policies': {
        },
        'variables': {
            'eth_price': None,
            'market_price_twap': s_market_price_twap
        }
    },
    {
        'label': 'Aggregate states 1',
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
        'label': 'Debt Market Aggregate State',
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
            'RAI_balance': s_RAI_balance,
            'ETH_balance': s_ETH_balance
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
        Retrieve error terms required to compute the various control actions
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
        'label': 'Redemption Price & Rate',
        'details': """
        New redemption price & rate based on stability control action 
        """,
        'policies': {},
        'variables': {
            'redemption_price': update_redemption_price,
            'redemption_rate': update_redemption_rate
        }
    },
    #################################################################
    {
        'label': 'Aggregate W',
        'policies': {},
        'variables': {
            'drip_in_rai': s_aggregate_drip_in_rai,
            'wipe_in_rai': s_aggregate_wipe_in_rai,
            'bite_in_rai': s_aggregate_bite_in_rai,
        }
    },
    {
        'label': 'Debt Market State Summary',
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
        'label': 'Debt Market Aggregate State (2)',
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
        'label': 'Aggregate User Action',
        'flags': {'extrapolation'},
        'description': """
        Modify the macro system state according to the
        Data-driven Linearized Aggregated Arbitrageur Model
        Reference: https://hackmd.io/w-vfdZIMTDKwdEupeS3qxQ
        """,
        'policies': {
            'user_action': p_user_action
        },
        'variables': {
            'ETH_balance': s_ETH_balance,
            'RAI_balance': s_RAI_balance,
            'cdps': s_CDP_action
        }
    }
]

partial_state_update_blocks = [psub
                               for psub
                               in partial_state_update_blocks
                               if psub.get('enabled, True') == True]
