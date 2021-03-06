"""
backtesting.py

Functions and definitions for calculating the validation loss of a
backtested simulation.
"""
from dataclasses import dataclass
from typing import Dict, Callable, List
import numpy as np
from pandas import DataFrame

MetricLossFunction = Callable[[DataFrame, DataFrame], float]


@dataclass
class ValidationMetricDefinition():
    metric_type: object
    loss_function: MetricLossFunction


def loss(true_value: np.ndarray,
         predicted_value: np.ndarray) -> np.ndarray:
    """
    Time-wise loss function.
    """
    residue = np.abs(true_value - predicted_value)
    return residue


def aggregate_loss(loss_series: np.ndarray) -> float:
    """
    Loss function for a time-series.
    """
    return sum(loss_series) / len(loss_series)


def generic_loss(y: np.ndarray,
                 y_hat: np.ndarray) -> float:
    y_error = loss(y, y_hat)
    agg_loss = aggregate_loss(y_error)
    return agg_loss


def generic_column_loss(sim_df,
                        test_df,
                        col: str) -> float:
    """
    Default loss function
    """
    y = test_df[col]
    y_hat = sim_df[col]
    return generic_loss(y, y_hat)


def generic_nested_metric_loss(col: str, key: str):
    def loss_function(sim_df, test_df) -> float:
        y = sim_df[col].map(lambda x: x[key])
        y_hat = test_df[col][key].map(lambda x: x[key])
        return generic_loss(y, y_hat)
    return loss_function


def generic_metric_loss(col: str) -> Callable[[DataFrame, DataFrame], float]:
    """
    Generates loss functions for a given column.
    """
    def loss_function(sim_df, test_df) -> float:
        return generic_column_loss(sim_df, test_df, col)
    return loss_function


def redemption_rate_loss(sim_df, test_df) -> float:
    y_error = np.abs(sim_df.redemption_rate - test_df.redemption_rate)
    agg_loss = aggregate_loss(y_error)
    return agg_loss


def market_price_loss(sim_df, test_df) -> float:
    y_error = np.abs(sim_df.market_price - sim_df.spot_price)
    agg_loss = aggregate_loss(y_error)
    return agg_loss


VALIDATION_METRICS = {
    'redemption_price': ValidationMetricDefinition(float, generic_metric_loss('redemption_price')),
    'redemption_rate': ValidationMetricDefinition(float, redemption_rate_loss),
    # 'market_price': ValidationMetricDefinition(float, market_price_loss)
}


def validation_loss(validation_metrics: Dict[str, float]) -> float:
    """
    Compute validation loss for a simulation.
    """
    return np.mean(list(validation_metrics.values()))


def simulation_metrics_loss(sim_df: DataFrame,
                            test_df: DataFrame) -> Dict[str, float]:
    """
    Computes all validation metrics for a simulation dataframe,
    given a test dataset.
    """
    metrics_loss = {}
    for metric, definition in VALIDATION_METRICS.items():
        loss = definition.loss_function(sim_df, test_df) # type: ignore
        metrics_loss[metric] = loss
    return metrics_loss


def simulation_loss(sim_df: DataFrame,
                    test_df: DataFrame) -> float:
    """
    Compute a simulation loss
    """
    metrics_loss = simulation_metrics_loss(sim_df.fillna(0), test_df.fillna(0))
    sim_loss = validation_loss(metrics_loss)
    return sim_loss
