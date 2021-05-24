# %%

from rai_digital_twin.execution_logic import extrapolation_cycle

df = extrapolation_cycle()
# %%
import plotly.express as px
# %%
fig_df = df.query('timestep > 0')
fig = px.line(fig_df,
              x='timestep',
              y=['eth_price', 'market_price'],
              log_y=True)
fig.show()
# %%
fig_df = df.query('timestep > 0')
fig = px.line(fig_df,
              x='timestep',
              y=['rai_reserve', 'eth_reserve', 'rai_debt', 'eth_locked'],
              log_y=True)
fig.show()

# %%
