from cadCAD.configuration.utils import config_sim
from cadCAD.configuration import Experiment


import importlib

class ConfigWrapper:
    '''
    The ConfigWrapper allows you to pass a cadCAD model (with a standard file structure) as an argument, and update the model and simulation configuration.
    Dictionaries, such as parameters and initial states would be merge updated, and all other options are overridden.
    It abstracts much of the cadCAD configuration away, and allows easily updating sets of parameters and initial states from the simulation notebooks.

    import models.system_model_v2 as system_model_v2
    e.g. system_model_v2_config = ConfigWrapper(system_model_v2)
    system_model_v2_config.append() # Append the simulation config to the global cadCAD configs list
    run() # Run the list of simulation configs stored in global cadCAD configs list
    '''
    def __init__(
            self,
            model,
            N=None,
            T=None,
            M={},
            initial_state={},
            partial_state_update_blocks=None,
            env_processes={},
            exp=Experiment()
        ):
        # Load the default model and simulation configuration from the model module
        m_state_variables = importlib.import_module(f'{model.__name__}.model.state_variables.init').state_variables
        m_psubs = importlib.import_module(f'{model.__name__}.model.partial_state_update_blocks').partial_state_update_blocks
        m_params = importlib.import_module(f'{model.__name__}.model.params.init').params
        m_sim_params = importlib.import_module(f'{model.__name__}.sim_params')
        
        # If either of Monte Carlo Runs or timesteps have been passed to the wrapper, override the default values
        self.N = N if N else m_sim_params.MONTE_CARLO_RUNS
        self.T = T if T else range(m_sim_params.SIMULATION_TIME_STEPS)
        
        # If a parameter dictionary has been passed to the wrapper, update the default parameters
        m_params.update(M)
        self.M = m_params
        
        # If a state variable dictionary has been passed to the wrapper, update the default initial state
        m_state_variables.update(initial_state)
        self.initial_state = m_state_variables
        
        # If a list of partial state update blocks has been passed to the wrapper, override the default value
        self.partial_state_update_blocks = partial_state_update_blocks if partial_state_update_blocks else m_psubs

        # Set any environment processes
        self.env_processes = env_processes
        # Set the cadCAD Experiment instance
        self.exp = exp

    def get_config(self):
        # Get the cadCAD simulation configuration dictionary
        # Constructed from N (number of runs), T (number of timesteps), and M (model parameters)
        return config_sim(
            {
                'N': self.N,
                'T': self.T,
                'M': self.M,
            }
        )[0]
    
    def append(self, sim_configs=None):
        '''
        Append a new simulation configuration to the global cadCAD configs list, and return the experiment instance
        '''
        if not isinstance(sim_configs, list):
            sim_configs = config_sim({'N': self.N, 'T': self.T, 'M': self.M})

        self.exp.append_configs(
            sim_configs=sim_configs,
            initial_state=self.initial_state,
            partial_state_update_blocks=self.partial_state_update_blocks,
            env_processes=self.env_processes,
        )

        return self.exp
