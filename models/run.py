import pandas as pd
import logging
from datetime import datetime
import time

from models.utils.process_results import drop_dataframe_midsteps
from models.config_wrapper import ConfigWrapper


def run(config: ConfigWrapper, drop_midsteps: bool=True, use_radcad=False) -> pd.DataFrame:
    config.append() # Append the simulation config to the cadCAD `configs` list

    # Configure the Python logging framework, logs saved to `logs/` directory with the current timestamp.
    # Call logging info/debug/warning methods in model methods.
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(filename=f'logs/simulation-{datetime.now()}.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logging.info('Started simulation')
    start = time.time()

    if use_radcad:
        from radcad import Model, Simulation, Experiment
        from radcad.engine import Engine, Backend

        model = Model(
            initial_state=config.initial_state,
            state_update_blocks=config.partial_state_update_blocks,
            params=config.M
        )
        simulation = Simulation(model=model, timesteps=len(list(config.T)), runs=config.N)
        experiment = Experiment([simulation])
        experiment.engine = Engine(
            backend=Backend.PATHOS, # Backend.SINGLE_PROCESS
            raise_exceptions=False,
            deepcopy=False,
        )

        raw_result = experiment.run()
        exceptions = experiment.exceptions

        # Convert the raw results to a Pandas dataframe
        df = pd.DataFrame(raw_result)
        # If enabled, drop the simulation result midsteps
        # i.e. only keep the final state at the end of a simulation timestep
        df = drop_dataframe_midsteps(df) if drop_midsteps else df.reset_index()

        return (df, exceptions, None)
    else:
        from cadCAD.engine import ExecutionMode, ExecutionContext, Executor
        from cadCAD.configuration import Experiment
        from cadCAD import configs
    
        # Set the cadCAD execution mode to local_mode - "Automatically selects Single Threaded or Multi-Process/Threaded Modes"
        # See https://github.com/cadCAD-org/cadCAD/blob/master/documentation/Simulation_Execution.md
        exec_mode = ExecutionMode()
        exec_context = ExecutionContext(exec_mode.local_mode)
        # Create a cadCAD simulation Executor instance, and set the cadCAD simulation configs list 
        run = Executor(exec_context=exec_context, configs=configs)

        # Execute the simulation, and return the raw results (list of dictionaries containing states)
        raw_result, tensor_field, sessions = run.execute()

        # Convert the raw results to a Pandas dataframe
        df = pd.DataFrame(raw_result)
        # If enabled, drop the simulation result midsteps
        # i.e. only keep the final state at the end of a simulation timestep
        df = drop_dataframe_midsteps(df) if drop_midsteps else df.reset_index()

        return (df, tensor_field, sessions)

    end = time.time()
    
    logging.info(f'Finished simulation in {end - start} seconds')
    print(f'Finished simulation in {end - start} seconds')
