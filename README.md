# reflexer
Reflexer Labs, RAI

# Modelling & Simulation

To run simulation:
```python
python3 run.py
```
or
```python
from run import run
drop_midsteps = True
result = run(drop_midsteps)
```

* `notebook.ipynb` - lab notebook for model simulation and visualization using cadCAD
* `run.py` - script to run simulation experiments
* `experiment/` - RAI model and simulation configuration
* `experiment/model` - model configuration (e.g. PSUBs)
* `experiment/model/parts` - model logic and state update functions
