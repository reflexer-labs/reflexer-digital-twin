from typing import List
from cadCAD_tools import generic_suf

# Meta stuff
from .parts.time import p_resolve_time_passed
from .parts.time import s_store_timedelta, s_update_cumulative_time

# Token State (Backtesting & Extrapolation)
from .parts.token_state import s_token_state
from .parts.token_state import p_backtesting, p_user_action

# Events
from .parts.governance import p_governance_events, s_pid_params

# Exogenous Info
from .parts.exogenous import p_exogenous

# Controller
from .parts.controllers import p_observe_errors, s_pid_error, s_pid_redemption


partial_state_update_blocks: List[dict] = [
    {
        'label': 'Time Tracking',
        'policies': {
            'time_process': p_resolve_time_passed
        },
        'variables': {
            'timedelta': s_store_timedelta,
            'cumulative_time': s_update_cumulative_time
        }
    },
        {
        'label': 'Governance & Backtesting',
        'policies': {
            'governance_events': p_governance_events,
            'backtesting_data': p_backtesting, # Only used on backtesting
            'exogenous data': p_exogenous

        },
        'variables': {
            'pid_params': s_pid_params,
            'token_state': s_token_state, # Only used on backtesting
            'eth_price': generic_suf('eth_price'),
            'market_price': generic_suf('market_price')
        }
    },
    {
        'label': 'Compute controller error',
        'policies': {
            'observe': p_observe_errors
        },
        'variables': {
            'pid_state': s_pid_error
        }
    },
    {
        'label': 'Compute controller Redemption Price & Rate',
        'policies': {},
        'variables': {
            'pid_state': s_pid_redemption
        }
    },
    {
        # Only used for extrapolation
        'label': 'Aggregate User Action',
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
