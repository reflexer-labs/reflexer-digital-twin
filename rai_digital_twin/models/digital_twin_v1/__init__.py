from .model.params import params as parameters
from .model.state_variables import state_variables as initial_state
from .model.partial_state_update_blocks import partial_state_update_blocks as timestep_block
from .sim_params import SIMULATION_TIME_STEPS as timesteps
from .sim_params import MONTE_CARLO_RUNS as samples



run_args = (initial_state, parameters, timestep_block, timesteps, samples)