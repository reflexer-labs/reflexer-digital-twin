Reflexer Labs, RAI
=======
Reflexer Labs, RAI

# Table of Contents

Each model is located under `models/_`, with a unique name for each experiment.

* `notebook.ipynb` - lab notebook for model simulation and visualization using cadCAD
* `models/run.py` - script to run simulation experiments
* `models/_/model` - model configuration (e.g. PSUBs, state variables)
* `models/_/model/parts` - model logic, state update functions, and policy functions

# Models

1. Validation model - `models/market_model`: various debt price test scenarios, used for validating full system model, and tuning PI controller
2. Verification model - `models/controller_model`: debt market ML model as debt price source, used for verifying Solidity implementation

Note: Both models share the same core logic, implemented in `models/market_model`. When custom logic and simulation config needs to be implemented to extend the validation model, this can be implemented in `models/controller_model`.

# Dependencies

You'll need Python 3+ in your environment.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
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
