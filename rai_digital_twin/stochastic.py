# %%

from rai_digital_twin.types import USD_per_ETH
from typing import Iterable
import pandas as pd
import numpy as np
from dataclasses import dataclass
from scipy.stats import gamma
import pymc3 as pm


@dataclass
class FitParams():
    shape: float
    scale: float


@dataclass
class FilterState():
    xhat: list[float]
    P: list[float]
    xhatminus: list[float]
    Pminus: list[float]
    K: list[float]


def kalman_filter(observations: list[float],
                  initialValue: float,
                  truthValues: np.ndarray = None) -> np.ndarray:
    '''
    Description:
    Function to create a Kalman Filter for smoothing currency timestamps in order to search for the
    intrinisic value.

    Parameters:
    observations: Array of observations, i.e. predicted secondary market prices.
    initialValue: Initial Starting value of filter
    truthValues: Array of truth values, i.e. GPS location or secondary market prices. Or can be left
    blank if none exist
    plot: If True, plot the observations, truth values and kalman filter.
    paramExport: If True, the parameters xhat,P,xhatminus,Pminus,K are returned to use in training.

    Example:
    xhat,P,xhatminus,Pminus,K = kalman_filter(observations=train.Close.values[0:-1],
                                              initialValue=train.Close.values[-1],paramExport=True)
    '''
    # intial parameters
    n_iter = len(observations)
    sz = (n_iter,)  # size of array
    if isinstance(truthValues, np.ndarray):
        x = truthValues  # truth value
    z = observations  # observations (normal about x, sigma=0.1)

    Q = 1e-5  # process variance

    # allocate space for arrays
    xhat = np.zeros(sz)      # a posteri estimate of x
    P = np.zeros(sz)         # a posteri error estimate
    xhatminus = np.zeros(sz)  # a priori estimate of x
    Pminus = np.zeros(sz)    # a priori error estimate
    K = np.zeros(sz)         # gain or blending factor

    R = 0.1**2  # estimate of measurement variance, change to see effect

    # intial guesses
    xhat[0] = initialValue
    P[0] = 1.0

    for k in range(1, n_iter):
        # time update
        xhatminus[k] = xhat[k-1]
        Pminus[k] = P[k-1]+Q

        # measurement update
        K[k] = Pminus[k]/(Pminus[k]+R)
        xhat[k] = xhatminus[k]+K[k]*(z[k]-xhatminus[k])
        P[k] = (1-K[k])*Pminus[k]
    return xhat


def kalman_filter_predict(xhat,
                          P,
                          xhatminus,
                          Pminus,
                          K,
                          observations,
                          truthValues=None) -> FilterState:
    '''
    Description:
    Function to predict a pre-trained Kalman Filter 1 step forward.

    Parameters:
    xhat: Trained Kalman filter values - array
    P: Trained Kalman variance - array
    xhatminus: Trained Kalman xhat delta - array
    Pminus: Trained Kalman variance delta - array
    K: Kalman gain - array
    observations: Array of observations, i.e. predicted secondary market prices.
    truthValues: Array of truth values, i.e. GPS location or secondary market prices. Or can be left
    blank if none exist
    paramExport: If True, the parameters xhat,P,xhatminus,Pminus,K are returned to use in next predicted step.

    Example:
    xhat,P,xhatminus,Pminus,K = kalman_filter_predict(xhatInput,PInput,
                                                      xhatminusInput,PminusInput,KInput,observation,
                                                       paramExport=True)
    '''
    # intial parameters
    if isinstance(truthValues, np.ndarray):
        x = truthValues  # truth value
    z = observations  # observations (normal about x, sigma=0.1)

    Q = 1e-5  # process variance

    R = 0.1**2  # estimate of measurement variance, change to see effect

    # time update
    xhatminus = np.append(xhatminus, xhat[-1])
    Pminus = np.append(Pminus, P[-1]+Q)

    # measurement update
    K = np.append(K, Pminus[-1]/(Pminus[-1]+R))
    xhat = np.append(xhat, xhatminus[-1]+K[-1]*(z[-1]-xhatminus[-1]))
    P = np.append(P, (1-K[-1])*Pminus[-1])
    return FilterState(xhat, P, xhatminus, Pminus, K)


def generate_eth_timeseries(filter_values: FilterState,
                            timesteps: int,
                            fit_params: FitParams) -> Iterable[tuple[list[float], FilterState]]:
    eth_values = []
    for _ in range(0, timesteps + 1):
        sample = np.random.gamma(fit_params.shape, fit_params.scale, 1)[0]
        eth_values.append(sample)
        new_state = kalman_filter_predict(filter_values.xhat,
                                          filter_values.P,
                                          filter_values.xhatminus,
                                          filter_values.Pminus,
                                          filter_values.K,
                                          eth_values)
        yield (eth_values, new_state)


def generate_eth_samples(fit_params: FitParams,
                         timesteps: int,
                         samples: int,
                         initial_value: USD_per_ETH = None) -> Iterable[np.ndarray]:
    for run in range(0, samples):
        np.random.seed(seed=run)

        buffer_for_transcients = 100
        X = np.random.gamma(fit_params.shape,
                            fit_params.scale,
                            timesteps + buffer_for_transcients)

        # train kalman
        xhat = kalman_filter(observations=X[0:-1],
                             initialValue=X[-1])

        xhat = xhat[buffer_for_transcients:]
        
        # Align predictions with the initial value
        if initial_value is None:
            pass
        else:
            xhat += (initial_value - xhat[0])

        yield xhat


def fit_eth_price(X: np.ndarray) -> FitParams:
    """
    Perform Bayesian Inference on the ETH time series
    """
    model = pm.Model()
    with model:
        alpha = pm.Exponential('alpha', lam=2)
        beta = pm.Exponential('beta', lam=.1)
        g = pm.Gamma('g', alpha=alpha, beta=beta, observed=X)
        # BUG: we're limited for 1 core for now
        trace = pm.sample(5000, return_inferencedata=True, cores=1)

    
    a = np.mean(trace.posterior.alpha)
    b = np.mean(trace.posterior.beta)

    fit_params = FitParams(shape=a, scale=1 / b)
    return fit_params


def fit_predict_eth_price(X: np.ndarray,
                          timesteps: int,
                          samples: int,
                          initial_value: USD_per_ETH) -> tuple[np.ndarray, ...]:

    fit_params = fit_eth_price(X)
    results = tuple(generate_eth_samples(fit_params,
                                         timesteps,
                                         samples,
                                         initial_value))
    return results
