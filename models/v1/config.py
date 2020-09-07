from cadCAD.configuration.utils import config_sim
from cadCAD.configuration import Experiment
from cadCAD import configs

from model.state_variables import state_variables
from model.partial_state_update_blocks import partial_state_update_blocks
from model.parts.sys_params import params
from sim_params import SIMULATION_TIME_STEPS, MONTE_CARLO_RUNS


class Config:
    def __init__(
            self,
            N=MONTE_CARLO_RUNS,
            T=range(SIMULATION_TIME_STEPS),
            M=params,
            merge_params=False,
            initial_state=state_variables,
            partial_state_update_blocks=partial_state_update_blocks,
            env_processes={}
        ):
        self.N = N
        self.T = T

        if merge_params:
            self.M = params.update(M)
        else:
            self.M = M

        self.initial_state = initial_state
        self.partial_state_update_blocks = partial_state_update_blocks
        self.env_processes = env_processes
    
    def append(self, clear_configs=False):
        if clear_configs:
            del configs[:]
        
        sim_config = config_sim(
            {
                'N': self.N,
                'T': self.T,
                'M': self.M,
            }
        )

        exp = Experiment()
        exp.append_configs(
            sim_configs=sim_config,
            initial_state=self.initial_state,
            partial_state_update_blocks=self.partial_state_update_blocks,
            env_processes=self.env_processes,
        )

        return configs
