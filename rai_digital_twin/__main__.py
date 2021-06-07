from rai_digital_twin.execution_logic import extrapolation_cycle
import click
import os 


@click.command()
@click.option('-l', '--use-last-data', 'use_last_data', is_flag=True)
def main(use_last_data) -> None:
    extrapolation_cycle(use_last_data=use_last_data)

    # %%


if __name__ == "__main__":
    main()
