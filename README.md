# Reflexer, RAI

![RAI laws of motion](diagrams/laws_of_motion.png)
![Shock metrics](exports/shock_metrics-tuned.png)

## Table of Contents

Each model is located under `models/_`, with a unique name for each experiment.

* `notebook.ipynb` - lab notebook for model simulation and visualization using cadCAD
* `models/run.py` - script to run simulation experiments
* `models/_/model` - model configuration (e.g. PSUBs, state variables)
* `models/_/model/parts` - model logic, state update functions, and policy functions

## Models

1. `models/system_model` / `notebook_validation.ipynb` - full system model with parameters for selecting & testing subsystems, such as the controller, the debt price regression model, and the fitted market model.

# Notebooks

1. [Market Price Driven Model: PI Controller Tuning](notebook_validation_market_price.ipynb)
    * The purpose of this experiment is to tune and test the PI controller, by driving the market price directly.
1. [Debt Price Driven Model: PI Controller Tuning](notebook_validation_debt_price.ipynb)
    * The purpose of this experiment is to tune and test the PI controller, by driving the debt price directly.
2. [Debt Price Model & Market Model Validation](notebook_validation_regression.ipynb)
    * The purpose of this experiment, is to validate the system model, using a debt market regression model trained using historical data.

### System Dependencies

* `swig` for `auto-sklearn` Python library. Use `brew install swig@3` or:

```
apt-get remove swig
apt-get install swig3.0
ln -s /usr/bin/swig3.0 /usr/bin/swig
```

* `truffle` for running the Solidity simulations:

```
npm install -g truffle
```

## Dependencies

You'll need Python 3+ and NodeJS/NPM (v10.13.0) in your environment.

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install wheel
pip3 install -r requirements.txt
jupyter labextension install jupyterlab-plotly@4.9.0 # --minimize=False
python -m ipykernel install --user --name python-reflexer --display-name "Python (Reflexer)"
jupyter-lab
```

## Running Jupyter Notebooks

```bash
source venv/bin/activate
jupyter-lab
```

## Modelling & Simulation

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

## Solidity / cadCAD Simulation

```bash
cd ./cross-model/truffle
npm install
npm setup-network
# Open and run notebook_solidity_validation.ipynb
```

## System Shock Tests

See `test/run_shock_tests.py` for the set of Ki and Kp parameter sweeps.

```bash
python test/run_shock_tests.py
```

Outputs:
* `exports/_.png` - metric grid for each set of parameters
* `shock_tests.ipynb` - template notebook for running test and generating grid

# Simulation Profiling

```python
python3 -m cProfile -s time models/run.py
```
