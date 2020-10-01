Reflexer Labs, RAI
=======

# Table of Contents

Each model is located under `models/_`, with a unique name for each experiment.

* `notebook.ipynb` - lab notebook for model simulation and visualization using cadCAD
* `models/run.py` - script to run simulation experiments
* `models/_/model` - model configuration (e.g. PSUBs, state variables)
* `models/_/model/parts` - model logic, state update functions, and policy functions

# Models

1. Validation model - `models/market_model` / `notebook_validation.ipynb`: various debt price test scenarios, used for validating full system model, and tuning PI controller
  * PI Controller Tuning
  * Debt Price Model & Market Model Validation

# Dependencies

You'll need Python 3+ and NodeJS/NPM in your environment.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
jupyter labextension install jupyterlab-plotly@4.9.0 # --minimize=False
python -m ipykernel install --user --name python-reflexer --display-name "Python (Reflexer)"
jupyter-lab
```

## System Dependencies

* `swig` for `auto-sklearn` Python library: e.g. `brew install swig`

# Modelling & Simulation

To run simulation:
```python
python3 models/run.py
```
or
```python
from config_wrapper import ConfigWrapper
import market_model as market_model

market_simulation = ConfigWrapper(market_model)
market_simulation.append()

result = run(drop_midsteps=True)
```

# Simulation Profiling

```python
python3 -m cProfile -s time models/run.py
```
