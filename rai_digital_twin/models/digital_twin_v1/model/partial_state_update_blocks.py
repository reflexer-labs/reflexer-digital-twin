from typing import List
from cadCAD_tools import generic_suf

# Meta stuff
from .parts.time import p_resolve_time_passed
from .parts.time import s_store_timedelta, s_update_cumulative_time

# Backtesting
from .parts.backtesting import p_backtesting, s_token_state

# Extrapolation
# (...)

# Events
from .parts.governance import p_governance_events, s_pid_params
from .parts.user_action import p_user_action

# Exogenous Info
from .parts.exogenous import p_exogenous

# Controllers
from .parts.controllers import p_observe_errors, s_pid_error, s_pid_redemption


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
            'pid_params': s_pid_params
        }
    },
    {
        'label': 'Backtesting Exogenous Variables',
        'flags': {'backtesting'},
        'policies': {
            'backtesting_data': p_backtesting
        },
        'variables': {
            'token_state': s_token_state
        }
    },
    {
        'label': 'Exogenous Variables',
        'policies': {
            'exogenous data': p_exogenous
        },
        'variables': {
            'eth_price': generic_suf('eth_price'),
            'market_price': generic_suf('market_price')
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
            'pid_state': s_pid_error
        }
    },
    {
        'label': 'Redemption Price & Rate',
        'details': """
        New redemption price & rate based on stability control action 
        """,
        'policies': {},
        'variables': {
            'pid_state': s_pid_redemption
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
            'token_state': s_token_state
        }
    }
]

partial_state_update_blocks = [psub
                               for psub
                               in partial_state_update_blocks
                               if psub.get('enabled, True') == True]
