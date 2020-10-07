import pandas as pd

from cadCAD.engine import ExecutionMode, ExecutionContext, Executor
from cadCAD.configuration import Experiment
from cadCAD import configs

def run(drop_midsteps: bool=True) -> pd.DataFrame:
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
    import sys
    sys.path.append('./models')

    from config_wrapper import ConfigWrapper
    import options as options
    from utils.load_data import load_debt_price_data

    import system_model as system_model
    
    debt_price_source = options.DebtPriceSource.DEBT_MARKET_MODEL.value
    debt_price_data = load_debt_price_data(debt_price_source)

    minimum_timesteps = min([df.shape[0] for df in debt_price_data])
    SIMULATION_TIMESTEPS = range(minimum_timesteps)

    update_params = {
        options.DebtPriceSource.__name__: [debt_price_source],
        options.IntegralType.__name__: [options.IntegralType.LEAKY.value],
        'seconds_passed': [
            lambda timestep, df=df: int(df.iloc[timestep - 1]['seconds_passed'])
            for df in debt_price_data
        ],
        'price_move': [
            lambda timestep, df=df: float(df.iloc[timestep - 1]['price_move'])
            for df in debt_price_data
        ]
    }

    config = ConfigWrapper(system_model, M=update_params, T=SIMULATION_TIMESTEPS)
    config.append()

    results = run(drop_midsteps=True)
    print(results)
