# %%

import plotly.express as px
import pandas as pd
from rai_digital_twin.execution_logic import extrapolation_cycle

backtest_results, extrapolation_results = extrapolation_cycle()
# %%
(sim_df, test_df, raw_sim_df) = backtest_results
test_df = test_df.assign(seconds_passed=sim_df.seconds_passed)
sim_df = sim_df.assign(origin='backtest').iloc[1:]
test_df = test_df.assign(origin='data').iloc[1:]
extrapolation_results = extrapolation_results.assign(
    origin='extrapolation').iloc[1:].reset_index()
df = (pd.concat([sim_df, test_df])
      .reset_index()
      .assign(seconds_passed=lambda df: df.seconds_passed - df.seconds_passed[0])
      )

extrapolation_results.loc[:, 'seconds_passed'] += df.seconds_passed.max()
df = pd.concat([df, extrapolation_results])

df = (df
      .assign(hours_passed=lambda df: df.seconds_passed / (60 * 60))
      .assign(days_passed=lambda df: df.seconds_passed / (24 * 60 * 60)))
# %%
cols = ['redemption_rate',
        'eth_locked',
        'eth_price',
        'market_price',
        'redemption_price',
        'rai_reserve',
        'eth_reserve',
        'rai_debt',
        ]
fig_df = (df
          .melt(id_vars=['days_passed', 'origin'], value_vars=cols)
          )
fig = px.line(fig_df,
              x='days_passed',
              y='value',
              facet_row='variable',
              color='origin',
              width=1000,
              height=2000)
fig.update_yaxes(matches=None)
fig.update_xaxes(matches=None)
fig.show()

# %%
