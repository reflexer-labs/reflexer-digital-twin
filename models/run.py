import pandas as pd
import logging
from datetime import datetime

from cadCAD.engine import ExecutionMode, ExecutionContext, Executor
from cadCAD.configuration import Experiment
from cadCAD import configs

from models.utils.process_results import drop_dataframe_midsteps


def run(drop_midsteps: bool=True) -> pd.DataFrame:
    # Configure the Python logging framework, logs saved to `logs/` directory with the current timestamp.
    # Call logging info/debug/warning methods in model methods.
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(filename=f'logs/simulation-{datetime.now()}.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logging.info('Started simulation')
    
    # Set the cadCAD execution mode to local_mode - "Automatically selects Single Threaded or Multi-Process/Threaded Modes"
    # See https://github.com/cadCAD-org/cadCAD/blob/master/documentation/Simulation_Execution.md
    exec_mode = ExecutionMode()
    exec_context = ExecutionContext(exec_mode.local_mode)
    # Create a cadCAD simulation Executor instance, and set the cadCAD simulation configs list 
    run = Executor(exec_context=exec_context, configs=configs)

    # Execute the simulation, and return the raw results (list of dictionaries containing states)
    raw_result, tensor_field, sessions = run.execute()

    logging.info('Finished simulation')

    # Convert the raw results to a Pandas dataframe
    df = pd.DataFrame(raw_result)
    # If enabled, drop the simulation result midsteps
    # i.e. only keep the final state at the end of a simulation timestep
    df = drop_dataframe_midsteps(df) if drop_midsteps else df.reset_index()

    return (df, tensor_field, sessions)
