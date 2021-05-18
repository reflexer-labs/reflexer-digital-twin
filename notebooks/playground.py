# %%
import sys 
sys.path.append('..')

# %%
from rai_digital_twin import default_model
from cadCAD_tools import easy_run

# %%

results = easy_run(default_model.initial_state,
default_model.parameters,
default_model.timestep_block,
10,
1, 
assign_params=False)
results = default_model.post_processing(results)
results
# %%