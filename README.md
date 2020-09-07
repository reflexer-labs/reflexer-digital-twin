# reflexer
Reflexer Labs, RAI

# Table of Contents

Each model is located under `models/v_`, with a unique version for each experiment.

* `notebook.ipynb` - lab notebook for model simulation and visualization using cadCAD
* `models/v_/run.py` - script to run simulation experiments
* `models/v_/model` - model configuration (e.g. PSUBs, state variables)
* `models/v_/model/parts` - model logic, state update functions, and policy functions

# Dependencies

You'll need Python 3+ in your environment.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
jupyter-lab
```

# Modelling & Simulation

To run simulation:
```python
python3 models/v1/run.py
```
or
```python
from .models.v1.run import run
result = run(drop_midsteps=True)
```

# Simulation Profiling

```python
python3 -m cProfile -s time models/v1/run.py
```
