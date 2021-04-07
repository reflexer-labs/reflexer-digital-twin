# Meaning of the data files

Each row is a timestep. As of 07-Apr-2021, they're hourly data.
Each column is a MC realization.

- eth_values_mc.csv: ETH/USD exchange, hourly. Retrived from the Uniswap model. Unit: the raw one.
- buy_sell_mc.csv: Swap events for DAI.
- liquidity_mc.csv: Absolute Difference in DAI liquidity balance.