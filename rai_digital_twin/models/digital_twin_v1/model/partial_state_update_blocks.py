from typing import List
from cadCAD_tools import generic_suf

# Meta stuff
from .parts.time import p_resolve_time_passed
from .parts.time import s_store_timedelta, s_update_cumulative_time

# Backtesting
from .parts.backtesting import p_backtesting

# Extrapolation
# (...)

# Events
from .parts.governance import p_governance_events
from .parts.user_action import p_user_action, s_CDP_action

# Exogenous Info
from .parts.markets import s_ETH_balance, s_RAI_balance, s_market_price_twap

# Controllers
from .parts.controllers import p_observe_errors
from .parts.controllers import s_error_star_integral
from .parts.controllers import s_redemption_price, s_redemption_rate


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
            'ETH_balance': generic_suf('ETH_balance')
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
    #################################################################
    {
        'label': 'Compute error',
        'details': """
        Retrieve error terms required to compute the various control actions
        """,
        'policies': {
            'observe': p_observe_errors
        },
        'variables': {
            'error_star': generic_suf('error_star'),
            'error_star_integral': s_error_star_integral,
        }
    },
    {
        'label': 'Redemption Price & Rate',
        'details': """
        New redemption price & rate based on stability control action 
        """,
        'policies': {},
        'variables': {
            'redemption_price': s_redemption_price,
            'redemption_rate': s_redemption_rate
        }
    },
    {
        'label': 'Aggregate User Action',
        'flags': {'extrapolation'},
        'description': """
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
