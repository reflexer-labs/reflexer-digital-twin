"""
backtesting.py

Functions and definitions for calculating the validation loss of a
backtested simulation.
"""
from dataclasses import dataclass
from typing import Dict, NamedTuple, Callable
from collections import namedtuple
import numpy as np

MetricLossFunction = Callable[[object, object], float]


@dataclass
class ValidationMetricDefinition():
    metric_type: object
    loss_function: callable


def loss(true_value: float,
         predicted_value: float) -> float:
    """
    Time-wise loss function.
    """
    return (true_value - predicted_value) ** 2


def aggregate_loss(loss_series: np.array) -> float:
    """
    Loss function for a time-series.
    """
    return loss_series.mean()


def generic_loss(sim_df,
                 test_df,
                 col: str) -> float:
    """
    Default loss function
    """
    y = test_df[col]
    y_hat = sim_df[col]
    y_error = loss(y, y_hat)
    agg_loss = aggregate_loss(y_error)
    return agg_loss


def generic_metric_loss(col: str) -> Callable[[str], MetricLossFunction]:
    """
    Generates loss functions for a given column.
    """
    def loss_function(sim_df, test_df) -> float:
        return generic_loss(sim_df, test_df, col)
    return loss_function


VALIDATION_METRICS = {
    'redemption_price': ValidationMetricDefinition(float, generic_metric_loss('redemption_price')),
    'redemption_rate': ValidationMetricDefinition(float, generic_metric_loss('redemption_rate'))
}


def validation_loss(validation_metrics: Dict[str, float]) -> float:
    """
    Compute validation loss for a simulation.
    """
    return np.mean(list(validation_metrics.values()))


def simulation_metrics_loss(sim_df,
                            test_df) -> Dict[str, float]:
    """
    Computes all validation metrics for a simulation dataframe,
    given a test dataset.
    """
    metrics_loss = {}
    for metric, definition in VALIDATION_METRICS.items():
        loss = definition.loss_function(sim_df, test_df)
        metrics_loss[metric] = loss
    return metrics_loss


def simulation_loss(sim_df: object,
                    test_df: object) -> float:
    """
    Compute a simulation loss
    """
    metrics_loss = simulation_metrics_loss(sim_df, test_df)
    sim_loss = validation_loss(metrics_loss)
    return sim_loss
