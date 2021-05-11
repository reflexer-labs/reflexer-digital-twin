from rai_digital_twin.types import CDP


def p_backtesting(params, _2, _3, state):
    t = state['timestep']

    """
    """
    backtesting_data = params['backtesting_data']
    current_data = backtesting_data[t]
    return current_data


def s_cdp_backtesting(_1, _2, _3, _4, signal):
    aggregate_cdp = CDP(open=1,
                        time=0,
                        locked=signal['eth_collateral'],
                        drawn=signal['rai_drawn'],
                        wiped=0.0,
                        freed=0.0,
                        w_wiped=0.0,
                        dripped=0.0,
                        v_bitten=0.0,
                        u_bitten=0.0,
                        w_bitten=0.0)

    return ('cdp', aggregate_cdp)
