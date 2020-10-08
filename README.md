Reflexer Labs, RAI
=======

# Table of Contents

Each model is located under `models/_`, with a unique name for each experiment.

* `notebook.ipynb` - lab notebook for model simulation and visualization using cadCAD
* `models/run.py` - script to run simulation experiments
* `models/_/model` - model configuration (e.g. PSUBs, state variables)
* `models/_/model/parts` - model logic, state update functions, and policy functions

# Models

1. `models/system_model` / `notebook_validation.ipynb` - full system model with parameters for selecting & testing subsystems, such as the controller, the debt price regression model, and the fitted market model.

# Notebooks

1. [Market Price Driven Model: PI Controller Tuning](notebook_validation_market_price.ipynb)
    * The purpose of this experiment is to tune and test the PI controller, by driving the market price directly.
1. [Debt Price Driven Model: PI Controller Tuning](notebook_validation_debt_price.ipynb)
    * The purpose of this experiment is to tune and test the PI controller, by driving the debt price directly.
2. [Debt Price Model & Market Model Validation](notebook_validation_regression.ipynb)
    * The purpose of this experiment, is to validate the system model, using a debt market regression model trained using historical data.

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
