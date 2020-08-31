from cadCAD.configuration.utils import config_sim
from cadCAD.configuration import Experiment

from .model.state_variables import state_variables
from .model.partial_state_update_blocks import partial_state_update_blocks
from .model.parts.sys_params import params

from .sim_params import SIMULATION_TIME_STEPS, MONTE_CARLO_RUNS

sim_config = config_sim (
    {
        'N': MONTE_CARLO_RUNS,
        'T': range(SIMULATION_TIME_STEPS),
        'M': params,
    }
)

exp = Experiment()
exp.append_configs(
    sim_configs=sim_config,
    initial_state=state_variables,
    partial_state_update_blocks=partial_state_update_blocks
)
