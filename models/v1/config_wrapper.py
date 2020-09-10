from cadCAD.configuration.utils import config_sim
from cadCAD.configuration import Experiment

from model.state_variables import state_variables
from model.partial_state_update_blocks import partial_state_update_blocks
from model.parts.sys_params import params
from sim_params import SIMULATION_TIME_STEPS, MONTE_CARLO_RUNS


class ConfigWrapper:
    def __init__(
            self,
            N=MONTE_CARLO_RUNS,
            T=range(SIMULATION_TIME_STEPS),
            M=params,
            merge_params=False,
            initial_state=state_variables,
            partial_state_update_blocks=partial_state_update_blocks,
            env_processes={},
            exp=Experiment()
        ):
        self.N = N
        self.T = T

        if merge_params:
            params.update(M)
            self.M = params
        else:
            self.M = M

        self.initial_state = initial_state
        self.partial_state_update_blocks = partial_state_update_blocks
        self.env_processes = env_processes
        self.exp = exp

    def get_config(self):
        return config_sim(
            {
                'N': self.N,
                'T': self.T,
                'M': self.M,
            }
        )[0]
    
    def append(self, sim_configs=None):
        if not isinstance(sim_configs, list):
            sim_configs = config_sim({'N': self.N, 'T': self.T, 'M': self.M})

        self.exp.append_configs(
            sim_configs=sim_configs,
            initial_state=self.initial_state,
            partial_state_update_blocks=self.partial_state_update_blocks,
            env_processes=self.env_processes,
        )

        return self.exp
