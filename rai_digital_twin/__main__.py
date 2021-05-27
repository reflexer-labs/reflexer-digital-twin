from .execution_logic import extrapolation_cycle
import plotly.express as px
import pandas as pd
from rai_digital_twin.execution_logic import extrapolation_cycle
import click


@click.command()
@click.option('-v', '--viz', is_flag=True)
def main(viz):
    backtest_results, extrapolation_results = extrapolation_cycle()

    if viz:
        (sim_df, test_df, raw_sim_df) = backtest_results
        test_df = (test_df.assign(seconds_passed=sim_df.seconds_passed)
                   .assign(run=0, subset=0, simulation=0))
        sim_df = sim_df.assign(origin='backtest').iloc[1:]
        test_df = test_df.assign(origin='data').iloc[1:]
        extrapolation_results = extrapolation_results.assign(
            origin='extrapolation').iloc[1:].reset_index()
        df = (pd.concat([sim_df, test_df])
              .reset_index()
              .assign(seconds_passed=lambda df: df.seconds_passed - df.seconds_passed[0])
              )

        extrapolation_results.loc[:,
                                  'seconds_passed'] += df.seconds_passed.max()
        df = pd.concat([df, extrapolation_results])

        df = (df
              .assign(hours_passed=lambda df: df.seconds_passed / (60 * 60))
              .assign(days_passed=lambda df: df.seconds_passed / (24 * 60 * 60)))
        # %%
        cols = ['eth_price',
                'market_price',
                'spot_price',
                'redemption_rate',
                'redemption_price',
                'rai_debt',
                'eth_locked',
                'rai_reserve',
                'eth_reserve',
                ]
        fig_df = (df
                  .melt(id_vars=['days_passed', 'origin'], value_vars=cols)
                  )
        fig = px.scatter(fig_df,
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


if __name__ == "__main__":
    main()
