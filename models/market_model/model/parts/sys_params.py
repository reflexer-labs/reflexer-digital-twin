from FixedPoint import FXnum
import numpy as np

import options as options
from constants import SPY, RAY

#assume
halflife = SPY / 52 #weeklong halflife
alpha = int(np.power(.5, float(1 / halflife)) * RAY)

params = {
    'expected_blocktime': [FXnum(15)], #seconds
    'minumum_control_period': [3600], #seconds
    'expected_control_delay': [1200], #seconds
    'derivative_smoothing': [1], #unitless
    'debt_market_std':[.001], #defined price units per hour
    'kp': [FXnum(.25/3600)], #proportional term for the stability controller: units 1/second
    'ki': [FXnum(.25/3600**2)], #integral term for the stability controller: units 1/seconds^2
    'kp-star': [FXnum(-0.5866)], #proportional term for the market process: units 1/second
    'ki-star': [FXnum(0.0032/(24*3600))], #integral term for the market process to target price: units 1/seconds^2 
    'kd-star': [FXnum(0.4858)], #derivative term for the market process to target price: unitless
    'kp-hat': [FXnum(0.6923)], #proportional term for the market process to the debt price: units 1/seconds
    'ki-hat': [FXnum(0.0841/(24*3600))], #integral term for the market process to the debt price: units 1/seconds^2
    'kd-hat': [FXnum(-0.3155)], #derivative term for the market process to the debt price: unitless
    'k0': [FXnum(0.2055)], #intercept for the market model: unit USD
    'k-autoreg-1': [FXnum(0.7922)], #autoregressive term for the market model: unitless
    'alpha': [alpha], #in 1/RAY
    'error_term': [lambda target, measured: target - measured],
    options.DebtPriceSource.__name__: [options.DebtPriceSource.DEFAULT.value],
    options.IntegralType.__name__: [options.IntegralType.LEAKY.value],
}
