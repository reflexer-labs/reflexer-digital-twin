from collections import namedtuple
from typing import Any, Tuple, NamedTuple, List

"""
Reflexer implementation: https://github.com/reflexer-labs/geb-uniswap-median/blob/master/src/UniswapConsecutiveSlotsPriceFeedMedianizer.sol
See https://uniswap.org/docs/v2/core-concepts/oracles/
"""


class UniswapObservation(NamedTuple):
    """
    
    """

    timestamp: int  # Unit: epochs
    price_0_cumulative: float  # Unit: ETH / RAI * epochs
    price_1_cumulative: float  # Unit: ETH / RAI * epochs


class ConverterFeedObservation(NamedTuple):
    """

    """

    timestamp: int
    time_adjusted_price: float


class UniswapOracle:
    """

    """

    def __init__(
        self,
        granularity: int = 5,
        window_size: int = 15 * 3600,
        max_window_size: int = 21 * 3600,
    ):
        self.default_amount_in = 1
        self.target_token = "rai"
        self.denomination_token = "eth"

        self.granularity = granularity
        self.window_size = window_size
        self.max_window_size = max_window_size

        self.last_update_time: int = 0
        self.updates: int = 0
        self.period_size = window_size / granularity
        self.median_price: float = 0

        self.uniswap_observations: List[UniswapObservation] = []
        self.converter_feed_observations: List[ConverterFeedObservation] = []
        self.converter_price_cumulative: float = 0.0

        self.price_0_cumulative: float = 0.0
        self.price_1_cumulative: float = 0.0

        assert self.granularity > 1
        assert self.window_size > 0
        assert self.max_window_size > self.window_size
        assert self.period_size == self.window_size / self.granularity
        assert (
            int(self.window_size / self.granularity) * self.granularity
            == self.window_size
        )

    def earliest_observation_index(self) -> int:
        if self.updates <= self.granularity:
            return 0
        else:
            return self.updates - int(self.granularity)

    def get_first_observations_in_window(
        self,
    ) -> Tuple[UniswapObservation, ConverterFeedObservation]:
        """
        Get the first Uniswap and Converter Feed Observations
        """

        earliest_observation_index = self.earliest_observation_index()

        first_uniswap_observation = self.uniswap_observations[
            earliest_observation_index
        ]

        first_converter_feed_observation = self.converter_feed_observations[
            earliest_observation_index
        ]

        return first_uniswap_observation, first_converter_feed_observation

    def update_observations(
        self,
        state: dict,
        time_elapsed_since_latest: int,
        uniswap_price_0_cumulative: float,
        uniswap_price_1_cumulative: float,
    ) -> None:
        """
        Updates the class observations and variables when given a new
        system state.
        """
        now = state["cumulative_time"]
        price_feed_value = state["eth_price"]
        new_time_adjusted_price = price_feed_value * time_elapsed_since_latest

        # Update observations
        self.converter_feed_observations.append(
            ConverterFeedObservation(now, new_time_adjusted_price)
        )
        self.uniswap_observations.append(
            UniswapObservation(
                now, uniswap_price_0_cumulative, uniswap_price_1_cumulative
            )
        )

        # Update cumm converte price
        self.converter_price_cumulative += new_time_adjusted_price

        #
        if self.updates >= self.granularity:
            (
                _,
                first_converter_feed_observation,
            ) = self.get_first_observations_in_window()

            self.converter_price_cumulative -= (
                first_converter_feed_observation.time_adjusted_price
            )

    def uniswap_compute_amount_out(
        self,
        price_cumulative_start: int,
        price_cumulative_end: int,
        time_elapsed: int,
        amount_in: float,
    ) -> float:
        """
        Get the time-averaged amount out for a initial amount in.
        """

        assert price_cumulative_end >= price_cumulative_start, (
            price_cumulative_end,
            price_cumulative_start,
        )

        
        assert time_elapsed > 0

        price_average = (price_cumulative_end - price_cumulative_start) / time_elapsed
        amount_out = price_average * amount_in
        return amount_out

    def converter_compute_amount_out(self, time_elapsed, amount_in):
        assert time_elapsed > 0
        price_average = self.converter_price_cumulative / time_elapsed
        amount_out = amount_in * price_average  # / converterFeedScalingFactor
        return amount_out

    def get_median_price(
        self, state: dict, price_0_cumulative: float, price_1_cumulative: float
    ) -> float:
        """

        """

        now: int = state["cumulative_time"]

        if self.updates > 1:
            first_uniswap_observation, _ = self.get_first_observations_in_window()

            time_since_first = now - first_uniswap_observation.timestamp
            token_0, _ = (
                self.target_token,
                self.denomination_token,
            )  # sortTokens(targetToken, denominationToken)

            if token_0 == self.target_token:
                uniswap_amount_out = self.uniswap_compute_amount_out(
                    first_uniswap_observation.price_0_cumulative,
                    price_0_cumulative,
                    time_since_first,
                    self.default_amount_in,
                )
            else:
                uniswap_amount_out = self.uniswap_compute_amount_out(
                    first_uniswap_observation.price_1_cumulative,
                    price_1_cumulative,
                    time_since_first,
                    self.default_amount_in,
                )
            return self.converter_compute_amount_out(
                time_since_first, uniswap_amount_out
            )
        else:
            pass

        return self.median_price

    def update_result(self, state: dict) -> None:
        """

        Output:
            Updated Uniswap observations & median price
        """
        now: int = state["cumulative_time"]

        last_update_time: int = self.last_update_time

        if len(self.uniswap_observations) == 0:
            time_elapsed_since_latest = now - last_update_time
        else:
            last_timestamp = self.uniswap_observations[-1].timestamp
            time_elapsed_since_latest = now - last_timestamp

        # Do not update if the elapsed time since last update
        # is below the period size.
        condition = len(self.uniswap_observations) > 0
        condition &= time_elapsed_since_latest < self.period_size
        if condition is True:
            return None

        # See https://github.com/Uniswap/uniswap-v2-periphery/blob/master/contracts/libraries/UniswapV2OracleLibrary.sol
        f = lambda a, b, c: c * a / b

        # Unit: ETH / RAI * epochs
        delta_0 = f(
            state["ETH_balance"], state["RAI_balance"], time_elapsed_since_latest
        )

        # Unit: RAI / ETH * epochs
        delta_1 = f(
            state["RAI_balance"], state["ETH_balance"], time_elapsed_since_latest
        )

        # Updates the oracle cumulative prices
        self.price_0_cumulative += delta_0
        self.price_1_cumulative += delta_1

        uniswap_price_0_cumulative, uniswap_price_1_cumulative = (
            self.price_0_cumulative,
            self.price_1_cumulative,
        )  # currentCumulativePrices() returns prices eth/rai & rai/eth

        #
        self.update_observations(
            state,
            time_elapsed_since_latest,
            uniswap_price_0_cumulative,
            uniswap_price_1_cumulative,
        )

        self.median_price = self.get_median_price(
            state, uniswap_price_0_cumulative, uniswap_price_1_cumulative
        )
        self.last_update_time = now
        self.updates += 1
