from .parts.controllers import *
from .parts.markets import *

partial_state_update_blocks = [
    {
        'details': """
        This block observes (or samples from data) the amount of time passed between events
        """,
        'policies': {'time_process':resolve_time_passed},
        'variables': {
            'timedelta': store_timedelta,
            'timestamp': update_timestamp,
            'blockheight': update_blockheight,
        }
    },
    
    {   
        'details': """
        This block observes (or samples from data) the change to the price implied by the debt price 
        """,
        'policies': {
            'debt_market': resolve_debt_price
        },
        'variables': {
            'debt_price': update_debt_price,
        }
    },
    {
        'details': """
        This block computes and stores the error terms
        required to compute the various control actions (including the market action)
        """,
        'policies': {'observe':observe_errors},
        'variables': {
            'error_star': store_error_star,
            'error_star_integral': update_error_star_integral,
            'error_star_derivative': update_error_star_derivative,
            'error_hat': store_error_hat,
            'error_hat_integral': update_error_hat_integral,
            'error_hat_derivative': update_error_hat_derivative,
        }
    },
    {
        'details': """
        This block applies the model of the market to update the market price 
        """,
        'policies': {},
        'variables': {
            'market_price': update_market_price,
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
    }
]
