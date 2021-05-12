import pandas as pd
import logging
from datetime import datetime
import time


def run(mod) -> pd.DataFrame:
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


    end = time.time()
    
    print("")
    logging.info(f'Finished simulation in {end - start} seconds')
    print(f'Finished simulation in {end - start} seconds')
    return output
