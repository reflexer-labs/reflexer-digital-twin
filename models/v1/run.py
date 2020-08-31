from cadCAD.engine import ExecutionMode, ExecutionContext, Executor

from . import config

from cadCAD import configs
import pandas as pd


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

    return df.reset_index()

if __name__ == '__main__':
    results = run(True)
    print(results)
