from collections import namedtuple

UniswapObservation = namedtuple('UniswapObservation', ['timestamp', 'price_0_cumulative', 'price_1_cumulative'])
ConverterFeedObservation = namedtuple('ConverterFeedObservation', ['timestamp', 'time_adjusted_price'])

class UniswapOracle():
    def __init__(self, granularity=5, window_size=3*24*3600, max_window_size=5*24*3600):
        self.default_amount_in = 1
        self.target_token = 'rai'
        self.denomination_token = 'eth'

        self.granularity = granularity
        self.window_size = window_size
        self.max_window_size = max_window_size

        self.last_update_time = 0
        self.updates = 0
        self.period_size = window_size / granularity
        self.median_price = 0
        
        self.uniswap_observations = []
        self.converter_feed_observations = []
        self.converter_price_cumulative = 0

        self.price_0_cumulative = 0
        self.price_1_cumulative = 0

        assert self.granularity > 1
        assert self.window_size > 0
        assert self.max_window_size > self.window_size
        assert self.period_size == self.window_size / self.granularity
        assert int(self.window_size / self.granularity) * self.granularity == self.window_size

    def earliest_observation_index(self):
        if (self.updates <= self.granularity):
            return 0
        else:
            return self.updates - int(self.granularity)

    def get_first_observations_in_window(self):
        earliest_observation_index = self.earliest_observation_index()
        first_uniswap_observation = self.uniswap_observations[earliest_observation_index]
        first_converter_feed_observation = self.converter_feed_observations[earliest_observation_index]
        return first_uniswap_observation, first_converter_feed_observation

    def update_observations(self, state, time_elapsed_since_latest, uniswap_price_0_cumulative, uniswap_price_1_cumulative):
        now = state['cumulative_time']
        price_feed_value = state['eth_price']
        new_time_adjusted_price = price_feed_value * time_elapsed_since_latest

        self.converter_feed_observations.append(
            ConverterFeedObservation(now, new_time_adjusted_price)
        )
        self.uniswap_observations.append(
            UniswapObservation(now, uniswap_price_0_cumulative, uniswap_price_1_cumulative)
        )
        self.converter_price_cumulative += new_time_adjusted_price

        if self.updates >= self.granularity:
            _, first_converter_feed_observation = self.get_first_observations_in_window()
            self.converter_price_cumulative -= first_converter_feed_observation.time_adjusted_price

    def uniswap_compute_amount_out(self, price_cumulative_start, price_cumulative_end, time_elapsed, amount_in):
        assert price_cumulative_end >= price_cumulative_start, (price_cumulative_end, price_cumulative_start)
        assert time_elapsed > 0
        price_average = (price_cumulative_end - price_cumulative_start) / time_elapsed
        amount_out = price_average * amount_in
        return amount_out

    def converter_compute_amount_out(self, time_elapsed, amount_in):
        assert time_elapsed > 0
        price_average = self.converter_price_cumulative / time_elapsed
        # TODO: review and confirm that scaling factor is for Solidity fixed point calculations
        amount_out = amount_in * price_average # / converterFeedScalingFactor
        return amount_out

    def get_median_price(self, state, price_0_cumulative, price_1_cumulative):
        now = state['cumulative_time']

        if self.updates > 1:
            first_uniswap_observation, _ = self.get_first_observations_in_window()
        
            time_since_first = now - first_uniswap_observation.timestamp
            token_0, _ = (self.target_token, self.denomination_token) # sortTokens(targetToken, denominationToken)

            if token_0 == self.target_token:
                uniswap_amount_out = self.uniswap_compute_amount_out(
                    first_uniswap_observation.price_0_cumulative,
                    price_0_cumulative,
                    time_since_first,
                    self.default_amount_in
                )
            else:
                uniswap_amount_out = self.uniswap_compute_amount_out(
                    first_uniswap_observation.price_1_cumulative,
                    price_1_cumulative,
                    time_since_first,
                    self.default_amount_in
                )
            return self.converter_compute_amount_out(time_since_first, uniswap_amount_out)
        return self.median_price


    def update_result(self, state):
        now = state['cumulative_time']

        last_update_time = self.last_update_time
        time_elapsed_since_latest = (now - last_update_time) if len(self.uniswap_observations) == 0 else (now - self.uniswap_observations[len(self.uniswap_observations) - 1].timestamp)
        
        if len(self.uniswap_observations) > 0:
            assert time_elapsed_since_latest >= self.period_size

        # See https://github.com/Uniswap/uniswap-v2-periphery/blob/master/contracts/libraries/UniswapV2OracleLibrary.sol
        self.price_0_cumulative += (state['ETH_balance'] / state['RAI_balance']) * time_elapsed_since_latest
        self.price_1_cumulative += (state['RAI_balance'] / state['ETH_balance']) * time_elapsed_since_latest
        uniswap_price_0_cumulative, uniswap_price_1_cumulative = (self.price_0_cumulative, self.price_1_cumulative) # currentCumulativePrices() returns prices eth/rai & rai/eth

        self.update_observations(state, time_elapsed_since_latest, uniswap_price_0_cumulative, uniswap_price_1_cumulative)

        self.median_price = self.get_median_price(state, uniswap_price_0_cumulative, uniswap_price_1_cumulative)
        self.last_update_time = now
        self.updates += 1
