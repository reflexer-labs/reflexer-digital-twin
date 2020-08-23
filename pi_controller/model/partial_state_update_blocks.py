from .parts.controller import *

partial_state_update_blocks = [
    {
        'policies': {
        },
        'variables': {
            'timestep': update_timestep,
            'latest_deviation_type': update_latest_deviation_type,
            'time_since_deviation': update_time_since_deviation,
            'target_rate': update_target_rate,
            'target_price': update_target_price,
            'market_price': update_market_price
        }
    }
]
