from FixedPoint import FXnum
import numpy as np

import model.parts.options as options
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
    'kp-star': [FXnum(0.25/3600)], #proportional term for the market process: units 1/second
    'ki-star': [FXnum(0)], #integral term for the market process to target price: units 1/seconds^2 
    'kd-star': [FXnum(.25)], #derivative term for the market process to target price: unitless
    'kp-hat': [FXnum(0.25/3600)], #proportional term for the market process to the debt price: units 1/seconds
    'ki-hat': [FXnum(0)], #integral term for the market process to the debt price: units 1/seconds^2
    'kd-hat': [FXnum(.1)], #derivative term for the market process to the debt price: unitless
    'alpha': [alpha], #in 1/RAY
    options.DebtPriceSource.__name__: [options.DebtPriceSource.DEFAULT],
    options.IntegralType.__name__: [options.IntegralType.LEAKY],
}
