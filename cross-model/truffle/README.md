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
