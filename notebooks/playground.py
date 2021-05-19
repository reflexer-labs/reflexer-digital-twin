# %%
from rai_digital_twin import prepare_data
import sys

import rai_digital_twin 
sys.path.append('..')

# %%
from rai_digital_twin import default_model
from cadCAD_tools import easy_run

from rai_digital_twin.execution_logic import *


backtest_model(*prepare())
# %%
BACKTESTING_DATA_PATH = '../data/states.csv'
GOVERNANCE_EVENTS_PATH = '../data/controller_params.csv'

# %%
