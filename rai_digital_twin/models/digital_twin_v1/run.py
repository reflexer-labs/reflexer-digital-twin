import pandas as pd
from cadCAD_tools import easy_run

def post_processing(results: pd.DataFrame) -> pd.DataFrame:

    df = results.copy().reset_index(drop=True)
    
    DROP_COLS = {'exogenous_data',
                 'backtesting_data',
                 'governance_events',
                 'heights'}

    DROP_COLS &= set(df.columns)

    df = df.drop(columns=DROP_COLS)

    dataclasses_cols = {'pid_params',
                        'pid_state',
                        'token_state'}

    dataclasses_cols &= set(df.columns)

    to_concat = []
    for col in dataclasses_cols:
        col_df = pd.DataFrame(df[col].tolist())
        to_concat.append(col_df)
        df = df.drop(columns=[col])
    to_concat.append(df)
    clean_results = pd.concat(to_concat, axis=1)
    return clean_results.reset_index(drop=True)


def run_model(*args, **kwargs):
    results = easy_run(*args)
    return post_processing(results)
