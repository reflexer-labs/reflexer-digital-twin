from rai_digital_twin.models.digital_twin_v1.model.parts.controllers import *
from pytest import approx

def test_redemption_rate():
    params = {'ki': -0.01,
              'kp': 0.01,
              'controller_enabled': False,
              'control_period': 10}
    
    state = {'error_star': 5,
             'error_star_integral': 5,
             'cumulative_time': 11,
             'redemption_rate': 0.01}

    args = (params, None, None, state, None)
    new_redemption_rate = s_redemption_rate(*args)[-1]
    assert new_redemption_rate == 0.0

    params.update(controller_enabled=True)
    args = (params, None, None, state, None)
    new_redemption_rate = s_redemption_rate(*args)[-1]
    assert new_redemption_rate == state['redemption_rate']

    state.update(cumulative_time=params['control_period'])
    args = (params, None, None, state, None)
    new_redemption_rate = s_redemption_rate(*args)[-1]
    assert new_redemption_rate == approx(0.045)


def test_redemption_price():
    state = {'redemption_price': 5,
             'redemption_rate': 0.01,
             'timedelta': 10}
    
    args = (None, None, None, state, None)
    approx_price = (1 + state['redemption_rate'])
    approx_price **= state['timedelta']
    approx_price *= state['redemption_price']
    new_price = s_redemption_price(*args)[-1]
    assert new_price == approx(approx_price, rel=0.01)

    state.update(timedelta=10)
    args = (None, None, None, state, None)
    approx_price = (1 + state['redemption_rate'])
    approx_price **= state['timedelta']
    approx_price *= state['redemption_price']
    new_price = s_redemption_price(*args)[-1]
    assert new_price == approx(approx_price, rel=0.01)

    state.update(redemption_rate=0.1)
    args = (None, None, None, state, None)
    approx_price = (1 + state['redemption_rate'])
    approx_price **= state['timedelta']
    approx_price *= state['redemption_price']
    new_price = s_redemption_price(*args)[-1]
    assert new_price == approx(approx_price, rel=0.05)
    
    state.update(redemption_price=0.001)
    args = (None, None, None, state, None)
    approx_price = (1 + state['redemption_rate'])
    approx_price **= state['timedelta']
    approx_price *= state['redemption_price']
    new_price = s_redemption_price(*args)[-1]
    assert new_price == approx(approx_price, rel=0.05)
    

def test_integral():
    params = {'alpha': 1.0}
    state = {'error_star_integral': 0.0,
             'error_star': 0.0,
             'timedelta': 1,
             'leaky_integral_activated': True}
    signal = {'error_star': 1}

    expected_integral = state['error_star_integral']
    expected_integral += state['timedelta'] * (state['error_star'] + signal['error_star']) / 2
    args = (params, None, None, state, signal)
    new_integral = s_error_star_integral(*args)[-1]
    assert new_integral == approx(expected_integral)

    state.update(error_star=3.0, timedelta=7)
    expected_integral = state['error_star_integral']
    expected_integral += state['timedelta'] * (state['error_star'] + signal['error_star']) / 2
    args = (params, None, None, state, signal)
    new_integral = s_error_star_integral(*args)[-1]
    assert new_integral == approx(expected_integral)

    state.update(error_star_integral=7.0)
    expected_integral = state['error_star_integral']
    expected_integral += state['timedelta'] * (state['error_star'] + signal['error_star']) / 2
    args = (params, None, None, state, signal)
    new_integral = s_error_star_integral(*args)[-1]
    assert new_integral == approx(expected_integral)

    params.update(alpha=0.0)
    state.update(leaky_integral_activated=True)
    expected_integral = state['timedelta'] * (state['error_star'] + signal['error_star']) / 2
    args = (params, None, None, state, signal)
    new_integral = s_error_star_integral(*args)[-1]
    assert new_integral == approx(expected_integral)

    params.update(alpha=1.0)
    expected_integral = state['error_star_integral']
    expected_integral += state['timedelta'] * (state['error_star'] + signal['error_star']) / 2
    args = (params, None, None, state, signal)
    new_integral = s_error_star_integral(*args)[-1]
    assert new_integral == approx(expected_integral)

    params.update(alpha=0.3)
    expected_integral = state['error_star_integral'] * params['alpha'] ** state['timedelta']
    expected_integral += state['timedelta'] * (state['error_star'] + signal['error_star']) / 2
    args = (params, None, None, state, signal)
    new_integral = s_error_star_integral(*args)[-1]
    assert new_integral == approx(expected_integral)