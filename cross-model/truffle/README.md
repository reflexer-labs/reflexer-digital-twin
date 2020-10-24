# geb-rrfm-truffle-sims

This repo takes care of simulating and feeding oracle prices into GEB on-chain PID controllers.

## Setup

Install [Node.js](https://nodejs.org/en/download/), [ganache-cli](https://github.com/trufflesuite/ganache-cli) and [Truffle](https://www.trufflesuite.com/docs/truffle/getting-started/installation).

You can then run this in one terminal:

```
ganache-cli -d -e 1000000000
```

And then run ```npm install``` on this repo in order to install all the Node dependencies.

To run the actual simulations do:

```
truffle test
```

## PI Validator

The PI rate setter tests are in ```test/pi_raw_validator.js``` and ```test/pi_scaled_validator.js```.

All the parameters have been pre-tuned but you can play with them in order to run custom simulations against the PI controller smart contracts.

```
General Parameters

Kp - proportional gain (wad)
Ki - integral gain (wad)
integralPeriodSize - amount of time to wait between rate updates (seconds)
precomputedRateAllowedDeviation - deviation allowed between the contract computed "global" rate and the rate computed off-chain and then submitted into the PI contract (wad)
baseUpdateCallerReward - min amount of system coins offered to the caller that updates the rate (wad)
maxUpdateCallerReward - max amount of system coins offered to the caller that updates the rate (wad)
perSecondCallerRewardIncrease - per-second increase in the reward offered for updating the redemption rate (ray)
perSecondCumulativeLeak - per-second leak applied to the integral (ray)
noiseBarrier - noise filtering method (P + I must be greater than a specific % of the current redemption price) (wad)
feedbackOutputUpperBound - max possible value that the redemption rate can take (ray)
feedbackOutputLowerBound - min possible value that the redemption rate can take (ray)
minRateTimeline - minimum timeline over which the redemption rate can be calculated (seconds)
oracleInitialPrice - initial price that the system coin oracle will return (wad)
initialRedemptionPrice - initial redemption price (ray)
```

```
Scenario Specific Parameters

shockPrice - used when testing for huge market price shocks (whether negative or positive)
shockSteps - amount of iterations during which the system coin oracle will return the shockPrice
stepsPostShock - amount of iterations occuring after the shockSteps and during which the system coin oracle will return values that are as close as possible to the redemption price
printOverview - used in every scenario to indicate whether it should print the whole simulation outcome in the terminal after the sim is done running
printStep - used in every scenario to indicate whether it should print every step of a simulation
simDataFilePath - path to file where a specific simulation outcome will be saved
orclPrices - array of system coin oracle prices used in the sim running a predefined market scenario
priceLowerBound - used in the sim running with random oracle prices in order to indicate the lower bound for every generated price
priceUpperBound - used in the sim running with random oracle prices in order to indicate the upper bound for every generated price
delayLowerBound - this is the minimum delay possible in order to bound all randomly generated delays. Should be equal to or greater than integralPeriodSize
delayUpperBound - this is the maximum delay possible in order to bound all randomly generated delays. Should be equal to or greater than delayLowerBound
steps - total amount of steps that the simulation with randomly generated prices and delays will run
```

All the simulation results are stored in ```test/saved_sims```.
