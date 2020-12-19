import pandas as pd

def drop_dataframe_midsteps(df):
    max_substep = max(df.substep)
    is_droppable = (df.substep != max_substep)
    is_droppable &= (df.substep != 0)
    df = df.loc[~is_droppable]
    return df.reset_index()
