# cadCAD for System Design and Validation 

## Parameter selection under uncertainty
- cadCAD workflow rests upon a standardized engineering
template:
-- System goals are identified
-- Control parameters are identified
-- Environmental parameters (uncontrolled) are identified
-- Key performance indicators (KPIs) / metrics are identified
-- Simulations are conducted
-- Optimal parameters are selected

## cadCAD as Decision Support Software
The overall objective of the project is to provide Reflexer with a software Decision Support System implemented via cadCAD, that achieves two design goals. First, the DSS achieves the iimmediate project objective, which is to provide stakeholders with the optimal economic policy parameters that are required to help implement the RAI economic system system. Such parameters are unknown at the time of system design, and require estimation and/or optimization using the system representation that a DSS provides. 

Second, the ongoing project objective will be to address the fact that as the system changes over time, its optimal parameter values (and hence participant behavior) may also change. cadCAD's DSS representation is created with dynamic analysis in mind, allowing for periodic updating of parameters in response to real-time information from the system as it evolves over time. Such parameter updating allows the DSS to be used by individual miners, to assist in their own economic policy over time. 

For both of these project objectives, the DSS does not replace decision-making, nor does it automatically engage with the system itself to provide auto-correcting features. Rather, it acts as a `digital twin' of the system, that can be demonstrated to faithfully replicate those salient features that impact both parameter setting and system evolution over time.

## Simulation Methodology
In the cadCAD simulation methodology, we operate on four layers: Policies, Mechanisms, States, and Metrics. Information flows do not have explicit feedback loop unless noted. Policies determine the inputs into the system dynamics, and can come from user input, observations from the exogenous environment, or algorithms. Mechanisms are functions that take the policy decisions and update the States to reflect the policy level changes. States are variables that represent the system quantities at the given point in time, and Metrics are computed from state variables to assess the health of the system. Metrics can often be thought of as KPIs, or Key Performance Indicators.

The way to think of cadCAD modeling is analogous to machine learning pipelines which normally consist of multiple steps when training and running a deployed model. There is preprocessing, which includes segregating features between continuous and categorical, transforming or imputing data, and then instantiating, training, and running a machine learning model with specified hyperparameters. cadCAD modeling can be thought of in the same way as states, roughly translating into features, are fed into pipelines that have built-in logic to direct traffic between different mechanisms, such as scaling and imputation. Accuracy scores, ROC, etc are analogous to the metrics that can be configured on a cadCAD model, specifying how well a given model is doing in meeting its objectives. The parameter sweeping capability of cadCAD can be thought of as a grid search, or way to find the optimal hyperparameters for a system by running through alternative scenarios. A/B style testing that cadCAD enables is used in the same way machine learning models are A/B tested, except out of the box, in providing a side by side comparison of muliple different models to compare and contract performance. Utilizing the field of Systems Identification, dynamical systems models can be used to "online learn" by providing a feedback loop to generative system mechanisms.

The flexibility of cadCAD also enables the embedding of machine learning models into behavior policies or mechanisms for complex systems with an machine learning prediction component.


* Introduction to Non-determinism and Monte Carlo Runs with cadCAD: 
https://github.com/cadCAD-org/demos/blob/f11fc19375373d69c3decbfcad72b600a54b2f79/tutorials/robots_and_marbles/robot-marbles-part-4/robot-marbles-part-4.ipynb
* Introduction to Parameter sweeping in cadCAD: https://github.com/cadCAD-org/demos/blob/master/tutorials/robots_and_marbles/robot-marbles-part-7/robot-marbles-part-7.ipynb

## Monte Carlo Runs
Monte carlo runs are used for stochastic systems when the results can differ between runs.  The underlying concept is to use random sampling to help solve problems that are deterministic in nature. By the law of large numbers, the expected value of random variables can be approximated by taking the sample mean/median of independent samples of the variable. To find a reliable prediction of the future system movements, monte carlo runs are used to show the range of potential outputs, and what is most likely to occur, the median value. 

### General Monte Carlo steps 
- Define a domain of possible inputs
- Generate inputs randomly from a probability distribution over the domain
 - Perform a deterministic computation on the inputs
- Aggregate the results

Block Science has developed a series of plots to illustrate Monte Carlo runs over specific outcome features.


To learn more about Monte Carlo runs in general, visit the following resources:
* [Investopedia](https://www.investopedia.com/terms/m/montecarlosimulation.asp)
* [Wikipedia](https://en.wikipedia.org/wiki/Monte_Carlo_method)


## Parameter Sweeps
Parameter sweeps is a functionality in cadCAD that enables sensativity analysis, along with Monte Carlo runs, for the selection of system hyperparameters. A hyperparameter is a parameter whose value is used to control the learning process.


Sensitivity analysis can then be performed, by: 
- Selecting the specific hyperparameters that influence the goals of the system.
- Performing Monte Carlo simulations across a sweep of (one or more)  parameters. [See](https://press.princeton.edu/books/hardcover/9780691152875/structural-macroeconometrics) for a comprehensive introduction to Monte Carlo and other simulation techniques.}
- Collecting statistics of the of one or more KPIs, to identify the likely trend of the output metric(s) and associated variance, with the latter identified as the 'spread' of selected interdecile ranges.
- Selecting a new set of functional forms, repeating (1) - (3), and comparing the resulting responses across functional forms, by repeating step (4) for as many functional form combinations as are available.

cadCAD DSS facilitates this type of analysis because of its modularity---parameters can not only be swept for a given functional form specification, but exogenous processes can also be 'swapped' in and out of the simulation framework according to which process functional forms are of interest. This is in contrast to a framework which requires hard-wiring a simulation to an ad hoc (and potentially incorrect) representation of an exogenous, environmental process---the latter approach, while perhaps relatively faster to implement in a DSS, precludes the sensitivity analysis approach enumerated above. Moreover, should the hard-wired process later prove to be insufficient to model actual exogenous processes---perhaps due to 'drift' over time, or due to novel supply and/or demand shocks---it can be prohibitively costly to reprogram the DSS with an updated exogenous process. 
