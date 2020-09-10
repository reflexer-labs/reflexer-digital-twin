from cadCAD.engine import ExecutionMode, ExecutionContext, Executor
from cadCAD.configuration import Experiment
from config_wrapper import ConfigWrapper
from cadCAD import configs

import options

import pandas as pd


def run(clear_configs: bool=False, drop_midsteps: bool=True, configs_: []=[ConfigWrapper()]) -> pd.DataFrame:
    if clear_configs:
        del configs[:]
            
    # For each unique experiment, append the config
    for config in configs_:
        config.append()
    # configs_[0].append([config.get_config() for config in configs_])

    exec_mode = ExecutionMode()
    exec_context = ExecutionContext(exec_mode.local_mode)
    run = Executor(exec_context=exec_context, configs=configs)
    results = pd.DataFrame()

    (system_events, tensor_field, sessions) = run.execute()

    df = pd.DataFrame(system_events)

    if drop_midsteps:
        max_substep = max(df.substep)
        is_droppable = (df.substep != max_substep)
        is_droppable &= (df.substep != 0)
        df = df.loc[~is_droppable]

    return (df.reset_index(), tensor_field, sessions)

if __name__ == '__main__':
    debt_price_source_file = './test/data/debt-price-test-data.csv'
    debt_price_dataframe = pd.read_csv(debt_price_source_file)

    test_dfs = [debt_price_dataframe]

    minimum_timesteps = min([df.shape[0] for df in test_dfs])
    SIMULATION_TIMESTEPS = range(minimum_timesteps)

    update_params = {
        options.DebtPriceSource.__name__: [options.DebtPriceSource.EXTERNAL.value],
        options.IntegralType.__name__: [options.IntegralType.LEAKY.value],
        'seconds_passed': [
            lambda timestep, df=df: int(df.iloc[timestep - 1]['seconds_passed'])
            for df in test_dfs
        ],
        'price_move': [
            lambda timestep, df=df: float(df.iloc[timestep - 1]['price_move'])
            for df in test_dfs
        ]
    }

    # env_processes = {
    #     'seconds_passed': lambda state, _sweep, _value, df=debt_price_dataframe.copy(): int(df.iloc[state['timestep'] - 1]['seconds_passed']),
    #     'price_move': lambda state, _sweep, _value, df=debt_price_dataframe.copy(): float(df.iloc[state['timestep'] - 1]['price_move']),
    # }

    config = ConfigWrapper(T=SIMULATION_TIMESTEPS)

    results = run(drop_midsteps=True, _configs=[config])
    print(results)
