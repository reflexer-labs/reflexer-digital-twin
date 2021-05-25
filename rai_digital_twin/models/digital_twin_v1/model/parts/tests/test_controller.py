from rai_digital_twin.models.digital_twin_v1.model.parts.controllers import *
from pytest import approx


def test_redemption_rate():
    state = {'pid_state': ControllerState(1, 1.00, 5.0, 5.0),
             'pid_params': ControllerParams(-0.01, 0.01, 1.0, 10, False),
             'redemption_rate': 1.01,
             'timedelta_in_hours': 1}

    args = (None, None, None, state, None)
    new_redemption_rate = s_pid_redemption(*args)[-1].redemption_rate
    assert new_redemption_rate == 1.0
    
    state.update(pid_params=ControllerParams(-0.01, 0.0001, 1.0, 10, True))
    args = (None, None, None, state, None)
    expected = state['pid_state'].proportional_error
    expected *= state['pid_params'].kp
    expected += state['pid_state'].integral_error * state['pid_params'].ki / state['pid_params'].period
    expected += 1.0
    new_redemption_rate = s_pid_redemption(*args)[-1].redemption_rate
    assert new_redemption_rate == approx(expected)


def test_redemption_price():
    state = {'pid_state': ControllerState(5, 1.01, None, None),
             'pid_params': ControllerParams(0.0, 0.0, 0.0, 1, False),
             'cumulative_time': 15,
             'timedelta_in_hours': 10}

    args = (None, None, None, state, None)
    approx_price = state['pid_state'].redemption_rate
    approx_price **= state['timedelta_in_hours']
    approx_price *= state['pid_state'].redemption_price
    new_price = s_pid_redemption(*args)[-1].redemption_price
    assert new_price == approx(approx_price, rel=0.01)

    state.update(timedelta=10)
    args = (None, None, None, state, None)
    approx_price = state['pid_state'].redemption_rate
    approx_price **= state['timedelta_in_hours']
    approx_price *= state['pid_state'].redemption_price
    new_price = s_pid_redemption(*args)[-1].redemption_price
    assert new_price == approx(approx_price, rel=0.01)

    state.update(redemption_rate=0.1)
    args = (None, None, None, state, None)
    approx_price = state['pid_state'].redemption_rate
    approx_price **= state['timedelta_in_hours']
    approx_price *= state['pid_state'].redemption_price
    new_price = s_pid_redemption(*args)[-1].redemption_price
    assert new_price == approx(approx_price, rel=0.05)

    state.update(redemption_price=0.001)
    args = (None, None, None, state, None)
    approx_price = state['pid_state'].redemption_rate
    approx_price **= state['timedelta_in_hours']
    approx_price *= state['pid_state'].redemption_price
    new_price = s_pid_redemption(*args)[-1].redemption_price
    assert new_price == approx(approx_price, rel=0.05)


# def test_integral():
#     state = {'pid_state': ControllerState(0.0, 0.0, 0.0, 0.0),
#              'pid_params': ControllerParams(0.0, 0.0, 1.0, 10, True),
#              'timedelta': 1}
#     signal = {'error_star': 1}

#     expected_integral = state['error_star_integral']
#     expected_integral += state['timedelta'] * \
#         (state['error_star'] + signal['error_star']) / 2
#     args = (params, None, None, state, signal)
#     new_integral = s_pid_error(*args)[-1].integral_error
#     assert new_integral == approx(expected_integral)

#     state.update(error_star=3.0, timedelta=7)
#     expected_integral = state['error_star_integral']
#     expected_integral += state['timedelta'] * \
#         (state['error_star'] + signal['error_star']) / 2
#     args = (params, None, None, state, signal)
#     new_integral = s_error_star_integral(*args)[-1]
#     assert new_integral == approx(expected_integral)

#     state.update(error_star_integral=7.0)
#     expected_integral = state['error_star_integral']
#     expected_integral += state['timedelta'] * \
#         (state['error_star'] + signal['error_star']) / 2
#     args = (params, None, None, state, signal)
#     new_integral = s_error_star_integral(*args)[-1]
#     assert new_integral == approx(expected_integral)

#     params.update(alpha=0.0)
#     state.update(leaky_integral_activated=True)
#     expected_integral = state['timedelta'] * \
#         (state['error_star'] + signal['error_star']) / 2
#     args = (params, None, None, state, signal)
#     new_integral = s_error_star_integral(*args)[-1]
#     assert new_integral == approx(expected_integral)

#     params.update(alpha=1.0)
#     expected_integral = state['error_star_integral']
#     expected_integral += state['timedelta'] * \
#         (state['error_star'] + signal['error_star']) / 2
#     args = (params, None, None, state, signal)
#     new_integral = s_error_star_integral(*args)[-1]
#     assert new_integral == approx(expected_integral)

#     params.update(alpha=0.3)
#     expected_integral = state['error_star_integral'] * \
#         params['alpha'] ** state['timedelta']
#     expected_integral += state['timedelta'] * \
#         (state['error_star'] + signal['error_star']) / 2
#     args = (params, None, None, state, signal)
#     new_integral = s_error_star_integral(*args)[-1]
#     assert new_integral == approx(expected_integral)
