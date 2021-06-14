# Reflexer Digital Twin

## Introduction

The Reflexer Digital Twin is a comprehensive modular toolkit for performing automated routine tests and system predictions that are aware of the controller fundamentals as well as the available live data.

The backtesting and extrapolation components are powered by cadCAD, a framework for generalized dynamical systems that allows for expressing the behavioural and logical mechanisms behind crypto-economic systems.

![RAI Digital Twin Components Diagram](assets/dt-components.png)

Specifically, it accomplishes the following functions:

- Data Interface: The DT has integration with the same live data that the RAI controller, as well as integrations with Data Lakes for exporting result sets.
- Backtesting: The DT is able to verify the past controller behaviour to make sure that it is working as intended.
- System Identification: The DT is able to identify and quantify past patterns for usage in extrapolation and scientific contexts.
- Future State Extrapolation: The DT is able to make use of data-driven mechanisms in order to extrapolate and predict the system trajectory over the future.
- Report Generation: The DT is able to generate diagnostics and rich visualizations that informs about the state of the system with a acessible focus.

## Usage 

The Reflexer Digital Twin requires **Python 3.9** and all the dependencies at `requirements.txt` installed.

Clone the repo and pass: `python -m rai_digital_twin`

This will retrieve, prepare, backtest, fit and extrapolate over the existing data.

The generated data will be located at `data/runs`, while any reports will be located at `reports/`

As of now, it is possible to configure the DT parameters by directly modified the `rai_digital_twin/__main__.py` call on the `extrapolation_cycle()` call. Options can include:

- Number of Monte Carlo runs for the USD/ETH price
- Interval for retrieving and backtesting data
- Re-utilize existing past data rather than retrieving

### Execution

### Result Analysis

### Testing

The Reflexer Digital Twin uses `pytest` for unit and integration testing. In order to make use of it, just pass:

``python -m pytest``


## Components

### Reports

TODO

### Data interface

TODO

### Backtesting

TODO
### System Identification

TODO
### Future State Extrapolation

TODO

## Notebooks
* [data_acquisition.ipynb](notebooks/data_acquisition.ipynb) shows how the data was obtained and from which sources
* [Systems_Identification_Fitting.ipynb](notebooks/Systems_Identification_Fitting.ipynb) documents the iterative process of constructing the systems identification model at the heart of the Digital Twin
* [VAR_vs_VARMAX_evaluation.ipynb](notebooks/VAR_vs_VARMAX_evaluation.ipynb)is an experimental notebook determining if VAR or VARMAX was a better fit for 

## References

- Scope document: https://hackmd.io/NXJNI2YVQziB3STBNH2Wjw
- Lucid chart: https://lucid.app/lucidchart/invitations/accept/inv_20c6ce89-4331-4cad-b6f7-4486fc5b3937
- Backtesting scope: https://hackmd.io/G8YvwPAHSq-bDw_rtrJTrQ
- Data sources: https://hackmd.io/r-Wwag4rT5K3U6OuKricXg
