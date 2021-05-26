# %%

import plotly.express as px
import pandas as pd
from rai_digital_twin.execution_logic import extrapolation_cycle

df = extrapolation_cycle()
# %%
# %%
df = df.assign(hours_passed=lambda df: df.seconds_passed / 3600)

# %%
cols = {'eth_price',
        'market_price',
        'redemption_price',
        'redemption_rate',
        'rai_reserve', 'eth_reserve',
        'rai_debt',
        'eth_locked'}
fig_df = (df
          .melt(id_vars=['hours_passed'], value_vars=cols)
          )
fig = px.line(fig_df,
              x='hours_passed',
              y='value',
              facet_row='variable',
              height=2000)
fig.update_yaxes(matches=None)
fig.show()
