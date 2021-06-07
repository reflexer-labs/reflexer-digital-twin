from typing import List
from cadCAD_tools import generic_suf

# Meta stuff
from .parts.time import p_resolve_time_passed, s_seconds_passed, s_timedelta_in_hours

# Token State (Backtesting & Extrapolation)
from .parts.token_state import s_token_state
from .parts.token_state import p_backtesting, p_user_action

# Events
from .parts.governance import p_governance_events, s_pid_params

# Exogenous Info
from .parts.exogenous import p_exogenous, s_market_price
from .parts.markets import s_spot_price

# Controller
from .parts.controllers import p_observe_errors, s_pid_error, s_pid_redemption


partial_state_update_blocks: List[dict] = [
    {
        'label': 'Time Tracking',
        'policies': {
            'time_process': p_resolve_time_passed
        },
        'variables': {
            'seconds_passed': s_seconds_passed,
            'timedelta_in_hours': s_timedelta_in_hours
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
            'market_price': s_market_price,
        }
    },
    {
        'label': 'Compute controller error',
        'policies': {
            'observe': p_observe_errors
        },
        'variables': {
            'pid_state': s_pid_error,
            'spot_price': s_spot_price
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
                               if psub.get('enabled', True) == True]
