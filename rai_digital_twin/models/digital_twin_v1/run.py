import pandas as pd
from cadCAD_tools import easy_run

def post_processing(results: pd.DataFrame) -> pd.DataFrame:
    DROP_COLS = {'exogenous_data',
                 'backtesting_data',
                 'governance_events',
                 'heights'}

    DROP_COLS &= set(results.columns)

    results = results.drop(columns=DROP_COLS)

    dataclasses_cols = {'pid_params',
                        'pid_state',
                        'token_state'}

    to_concat = []
    for col in dataclasses_cols:
        col_df = pd.DataFrame(results[col].tolist())
        to_concat.append(col_df)
        results = results.drop(columns=[col])
    to_concat.append(results)
    clean_results = pd.concat(to_concat, join='inner', axis=1)
    return clean_results


def run_model(*args, **kwargs):
    results = easy_run(*args)
    return post_processing(results)
