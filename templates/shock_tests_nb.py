# %% [markdown]
# # Imports

# %%
from shared import *
from itertools import chain

# %% [markdown]
# # Parameters

# %% tags=["parameters"]

# %%
error_term = [
    lambda target, measured: target - measured,
    # lambda target, measured: (target - measured) / measured,
    # lambda target, measured: (target - measured) / target
]

# %%
integral_type = [options.IntegralType.LEAKY.value]

# %% [markdown]
# # Simulation Configuration

# %%
SIMULATION_TIMESTEPS = 24 * 30
MONTE_CARLO_RUNS = 4

# %%
shock_amplitudes = [0.1, 0.5, 1.0]
sinusoid_amplitude = 0.5
sinusoid_frequency = 0.05

shocks = list(
    chain(
        *[
            [
                lambda timestep, shock_amplitude=shock_amplitude: shock_amplitude
                if timestep in [50, 100, 150, 200, 251, 301, 351, 401]
                else (
                    -shock_amplitude
                    if timestep in [51, 101, 151, 201, 250, 300, 350, 400]
                    else 0
                ),
                lambda timestep, shock_amplitude=shock_amplitude: shock_amplitude
                if timestep == 50
                else (-shock_amplitude if timestep == SIMULATION_TIMESTEPS / 2 else 0),
                lambda timestep, shock_amplitude=shock_amplitude: shock_amplitude
                / 50
                * np.sin(timestep * sinusoid_frequency)
                if timestep <= SIMULATION_TIMESTEPS / 2
                else 0,
            ]
            for shock_amplitude in shock_amplitudes
        ]
    )
) + [
    lambda timestep: sinusoid_amplitude / 50 * np.sin(timestep * sinusoid_frequency),
    lambda timestep: sinusoid_amplitude / 50 * np.sin(timestep * sinusoid_frequency),
    lambda timestep: sinusoid_amplitude / 50 * np.sin(timestep * sinusoid_frequency),
]

control_delays = [(lambda _timestep: 1200) for _ in range(len(shocks) - 3)] + [
    lambda timestep: 3600
    if timestep in chain(range(50, 100), range(300, 350))
    else 1200,
    lambda timestep: 3600 * 2
    if timestep in chain(range(50, 100), range(300, 350))
    else 1200,
    lambda timestep: 3600 * 3
    if timestep in chain(range(50, 100), range(300, 350))
    else 1200,
]

# %%

import numpy as np
from models.constants import SPY, RAY

halflife = SPY / 52 #weeklong halflife
# alpha = int(np.power(.5, float(1 / halflife)) * RAY)
alpha = 1000000000000000000000000000

# %%

# Update parameter options
update_params = {
    # By using an Enum, we can self-document all possible options
    options.DebtPriceSource.__name__: [options.DebtPriceSource.EXTERNAL.value],
    options.MarketPriceSource.__name__: [options.MarketPriceSource.DEFAULT.value],
    options.IntegralType.__name__: integral_type,
    "controller_enabled": [True],
    # A lambda that takes the timestep and returns the corresponding value
    "expected_control_delay": control_delays,
    "price_move": shocks,
    "kp": [kp_param],
    "ki": [lambda control_period=3600: ki_param / control_period],
    # Select or sweep the error term calculation, as a lambda
    # e.g. p*-p vs (p*-p)/p vs (p*-p)/p*
    "error_term": error_term,
    "alpha": [alpha]
}

update_initial_state = {
    'target_price': 1.0,
    'market_price': 1.0,
    'debt_price': 1.0,
}

"""
The ConfigWrapper allows you to pass a model as an argument, and update the simulation configuration.
Maps (params, states) would be merge updated, and all other options are overrides.
"""
system_simulation = ConfigWrapper(
    system_model, M=update_params, initial_state=update_initial_state, N=MONTE_CARLO_RUNS, T=range(SIMULATION_TIMESTEPS)
)

# %% [markdown]
# # Simulation Execution

# %%
del configs[:]

system_simulation.append()

(data, tensor_field, sessions) = run(drop_midsteps=True)

# %% [markdown]
# # Data Analysis

# %%
df = data.copy()
df

# %%
kp = update_params["kp"][0]
ki = update_params["ki"][0](3600)

df = df.assign(**{'kp': kp, 'ki': ki})
df.to_parquet(f'exports/shock_datasets/kp_{kp}_ki_{ki}.parquet.gzip', compression='gzip')

# %%
df["target_rate_hourly"] = df.target_rate  # * 3600
df["error_star_derivative_scaled"] = df.error_star_derivative * 3600
df["error_hat_derivative_scaled"] = df.error_star_derivative * 3600

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

rows = len(shocks)

fig = make_subplots(
    rows=rows,
    cols=5,
    shared_xaxes=True,
    shared_yaxes="rows",
    horizontal_spacing=0.01,
    vertical_spacing=0.01,
    column_titles=[
        "Shock",
        "Response",
        "Over/undershoot",
        "Recovery metric",
        "Response time"
    ],
    row_titles=[
        "Impulse 0.01",
        "Step 0.01",
        "Sinusoid 0.01",
        "Impulse 0.5",
        "Step 0.5",
        "Sinusoid 0.5",
        "Impulse 1.0",
        "Step 1.0",
        "Sinusoid 1.0",
        "3600s control delay",
        "7200s control delay",
        "10800s control delay",
    ],
    specs=[
        [
            {"type": "xy"},
            {"type": "xy"},
            {"type": "indicator"},
            {"type": "indicator"},
            {"type": "indicator"},
        ]
        for _ in range(rows)
    ],
)

for subset in range(df.subset.max() + 1):
    dataset = df[df.subset == subset]

    dataset["relative_diff"] = df.market_price / df.debt_price
    
    overshoot_pct = (dataset.market_price.max() - dataset.debt_price.max()) / dataset.debt_price.max() * 100

    reasonable_steady_state_error = 0.01
    dataset["pct_error"] = dataset["error_hat"] / dataset["debt_price"]
    dataset["pct_error"] = dataset["pct_error"].abs()
    recovery_metric = (
        dataset[dataset.pct_error > reasonable_steady_state_error]
        .groupby(["run"])["timedelta"]
        .sum()
        .mean()
        / 3600
    )
    
    try:
        pv_initial = dataset['debt_price'].iloc[0]
        pv_max = dataset['debt_price'].max()

        target_initial = dataset[dataset.target_price > pv_initial].iloc[0]
        time_constant = dataset[dataset.target_price - pv_initial >= 0.63 * (pv_max - pv_initial)].iloc[0].timestamp - target_initial.timestamp
        time_constant = time_constant / pd.Timedelta(hours=1)
    except IndexError:
        time_constant = -1

    timesteps = dataset.timestep
    grouped = dataset.groupby("timestep", as_index=False)
    mean = grouped.mean()
    std = grouped.std()

    row = subset + 1
    show_legend = subset == 0

    col = 1
    fig.add_trace(
        go.Scatter(
            name="debt_price",
            x=dataset[dataset.run == 1].timestep,
            y=dataset[dataset.run == 1]["debt_price"],
            line_color="black",
            showlegend=False,
        ),
        row=row,
        col=col,
    )

    col = 2
    fig.add_trace(
        go.Scatter(
            name="debt_price",
            x=dataset["timestep"],
            y=mean["debt_price"],
            line_color="black",
            showlegend=show_legend,
        ),
        row=row,
        col=col,
    )
    fig.add_trace(
        go.Scatter(
            name="target_price",
            x=dataset["timestep"],
            y=mean["target_price"],
            line_color="red",
            showlegend=show_legend,
        ),
        row=row,
        col=col,
    )
    fig.add_trace(
        go.Scatter(
            name="market_price",
            x=dataset["timestep"],
            y=mean["market_price"],
            line_color="green",
            showlegend=show_legend,
        ),
        row=row,
        col=col,
    )

    col = 3
    fig.add_trace(
        go.Indicator(
            name="Over/undershoot",
            mode="number",
            value=overshoot_pct,
            number={"font": {"size": 20}, "suffix": "%"},
        ),
        row=row,
        col=col,
    )

    col = 4
    fig.add_trace(
        go.Indicator(
            name="Recovery metric",
            mode="number",
            value=recovery_metric,
            number={"font": {"size": 20}, "suffix": " hours"},
        ),
        row=row,
        col=col,
    )
    
    col = 5
    fig.add_trace(
        go.Indicator(
            name="Time constant",
            mode="number",
            value=time_constant,
            number={"font": {"size": 20}, "suffix": " hours"},
        ),
        row=row,
        col=col,
    )

fig.update_layout(
    title=f'Kp = {"{:.4E}".format(kp)}; Ki = {"{:.4E}".format(ki)}',
    height=3000,
    template="plotly_white",
)
fig.show()
fig.write_image(
    f'exports/shock_metrics/kp_{"{:.4E}".format(kp)}-ki_{"{:.4E}".format(ki)}.png',
    width="1800",
)
fig.write_html(
    f'exports/shock_metrics/kp_{"{:.4E}".format(kp)}-ki_{"{:.4E}".format(ki)}.html'
)

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

rows = len(shocks)

fig = make_subplots(
    rows=rows,
    cols=1,
    shared_xaxes=True,
    shared_yaxes="rows",
    horizontal_spacing=0.01,
    vertical_spacing=0.01,
    column_titles=[
        "Market price / Debt price"
    ],
    row_titles=[
        "Impulse 0.01",
        "Step 0.01",
        "Sinusoid 0.01",
        "Impulse 0.5",
        "Step 0.5",
        "Sinusoid 0.5",
        "Impulse 1.0",
        "Step 1.0",
        "Sinusoid 1.0",
        "3600s control delay",
        "7200s control delay",
        "10800s control delay",
    ],
    specs=[
        [
            {"type": "xy"},
        ]
        for _ in range(rows)
    ],
)

for subset in range(df.subset.max() + 1):
    dataset = df[df.subset == subset]

    dataset["relative_diff"] = df.market_price / df.debt_price
    
    overshoot_pct = (dataset.market_price.max() - dataset.debt_price.max()) / dataset.debt_price.max() * 100

    reasonable_steady_state_error = 0.01
    dataset["pct_error"] = dataset["error_hat"] / dataset["debt_price"]
    dataset["pct_error"] = dataset["pct_error"].abs()
    recovery_metric = (
        dataset[dataset.pct_error > reasonable_steady_state_error]
        .groupby(["run"])["timedelta"]
        .sum()
        .mean()
        / 3600
    )

    timesteps = dataset.timestep
    grouped = dataset.groupby("timestep", as_index=False)
    mean = grouped.mean()
    std = grouped.std()

    row = subset + 1
    show_legend = subset == 0

    col = 1
    fig.add_trace(
        go.Scatter(
            x=timesteps,
            y=mean["relative_diff"] + std["relative_diff"],
            name="mean + std",
            mode="lines",
            line_color="blue",
            showlegend=show_legend,
        ),
        row=row,
        col=col,
    )
    fig.add_trace(
        go.Scatter(
            x=timesteps,
            y=mean["relative_diff"],
            name="mean",
            fill="tonexty",
            mode="lines",
            line_color="blue",
            showlegend=show_legend,
        ),
        row=row,
        col=col,
    )
    fig.add_trace(
        go.Scatter(
            x=timesteps,
            y=mean["relative_diff"] - std["relative_diff"],
            name="mean - std",
            fill="tonexty",
            mode="lines",
            line_color="blue",
            showlegend=show_legend,
        ),
        row=row,
        col=col,
    )

fig.update_layout(
    title=f'Kp = {"{:.4E}".format(kp)}; Ki = {"{:.4E}".format(ki)}',
    height=3000,
    template="plotly_white",
)
fig.show()
fig.write_image(
    f'exports/shock_std/kp_{"{:.4E}".format(kp)}-ki_{"{:.4E}".format(ki)}.png',
    width="1800",
)
fig.write_html(
    f'exports/shock_std/kp_{"{:.4E}".format(kp)}-ki_{"{:.4E}".format(ki)}.html'
)
