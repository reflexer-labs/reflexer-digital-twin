from .parts.controller import *

partial_state_update_blocks = [
    {
        'policies': {},
        'variables': {
            'market_price': update_market_price,
        }
    },
    {
        'policies': {},
        'variables': {
            'target_rate': update_target_rate,
            'target_price': update_target_price,
        }
    },
    {
        'policies': {},
        'variables': {
            'error': update_error,
            'error_integral': update_error_integral,
        }
    }
]
