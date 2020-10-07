 
import numpy as np

import options as options
from constants import SPY, RAY

#assume
halflife = SPY / 52 #weeklong halflife
alpha = int(np.power(.5, float(1 / halflife)) * RAY)

params = {
    'expected_blocktime': [(15)], #seconds
    'minumum_control_period': [3600], #seconds
    'expected_control_delay': [1200], #seconds
    'derivative_smoothing': [1], #unitless
    'debt_market_std':[.001], #defined price units per hour
    'kp': [(6.944e-06)], #proportional term for the stability controller: units 1/USD
    'ki': [(60.0/(24*3600))], #integral term for the stability controller: units 1/(USD*seconds)
    'kp-star': [(-0.5866)], #proportional term for the market process: unitless
    'ki-star': [(0.0032/(24*3600))], #integral term for the market process to target price: units 1/seconds 
    'kd-star': [(0.4858*(24*3600))], #derivative term for the market process to target price: units seconds
    'kp-hat': [(0.6923)], #proportional term for the market process to the debt price: unitless
    'ki-hat': [(0.0841/(24*3600))], #integral term for the market process to the debt price: units 1/seconds
    'kd-hat': [(-0.3155*(24*3600))], #derivative term for the market process to the debt price: units seconds
    'k0': [(0.2055)], #intercept for the market model: unit USD
    'k-autoreg-1': [(0.7922)], #autoregressive term for the market model: unitless
    'alpha': [alpha], #in 1/RAY
    'error_term': [lambda target, measured: target - measured],
    options.DebtPriceSource.__name__: [options.DebtPriceSource.DEFAULT.value],
    options.IntegralType.__name__: [options.IntegralType.LEAKY.value],
    options.MarketPriceSource.__name__: [options.MarketPriceSource.DEFAULT.value],
    'controller_enabled': [True]
}
