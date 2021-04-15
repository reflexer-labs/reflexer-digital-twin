import pandas as pd

def drop_dataframe_midsteps(df):
    '''
    Drop the simulation result midsteps.
    i.e. only keep the final state at the end of a simulation timestep.
    '''
    max_substep = max(df.substep)
    is_droppable = (df.substep != max_substep)
    is_droppable &= (df.substep != 0)
    df = df.loc[~is_droppable]
    return df.reset_index()
