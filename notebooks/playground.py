# %%

import sys  # noqa
sys.path.append('..')  # noqa

# %%
import plotly.express as px
from rai_digital_twin.execution_logic import *
# %%
backtesting_df, governance_events = prepare()
# %%
backtest_results = backtest_model(backtesting_df, governance_events)
# %%
(sim_df, test_df) = backtest_results
sim_df = sim_df.assign(origin='backtest').iloc[1:]
test_df = test_df.assign(origin='data').iloc[1:]
backtest_df = (pd.concat([sim_df, test_df])
                 .reset_index()
                 .assign(hours_passed=lambda df: df.seconds_passed / (60 * 60))
               )
# %%
fig_df = backtest_df

fig = px.line(fig_df,
              x='index',
              y='redemption_price',
              color='origin',
              log_y=True)
fig.show()
# %%
fig_df = backtest_df.assign(redemption_rate=lambda df: df.redemption_rate + 1)

fig = px.line(fig_df,
              x='index',
              y='redemption_rate',
              log_y=True,
              color='origin')
fig.show()
# %%
id_cols = {'hours_passed'}
value_cols = {'kp', 'ki', 'leaky_factor', 'period', 'enabled'}
fig_df = (backtest_df.melt(id_cols, value_cols).query('hours_passed > 0'))

fig = px.scatter(fig_df,
                 x='hours_passed',
                 y='value',
                 facet_row='variable',
                 height=800)
fig.update_yaxes(matches=None)

fig.show()
# %%
