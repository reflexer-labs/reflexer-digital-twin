const RateSetter             = artifacts.require("RateSetter");
const MockOracleRelayer      = artifacts.require("MockOracleRelayer");
const MockTreasury           = artifacts.require("MockTreasury");
const MockFeed               = artifacts.require("MockFeed");
const ERC20                  = artifacts.require("ERC20");

const BN                     = require('bn.js');
const Web3                   = require("web3");

module.exports = function(deployer) {
  const web3 = new Web3();

  // Default params
  var WAD                              = new BN("1000000000000000000");
  var RAY                              = new BN("1000000000000000000000000000");

  var tokenSymbol                      = "RAI";

  var oracleInitialPrice               = new BN(4.2).mul(WAD);
  var initialRedemptionPrice           = new BN(4.2).mul(RAY);

  deployer.deploy(ERC20, tokenSymbol, tokenSymbol).then(function() {
  return deployer.deploy(MockFeed, oracleInitialPrice, true).then(function() {
  return deployer.deploy(MockTreasury, ERC20.address).then(function() {
  return deployer.deploy(MockOracleRelayer, initialRedemptionPrice).then(function() {
  }) }) }) })
};
