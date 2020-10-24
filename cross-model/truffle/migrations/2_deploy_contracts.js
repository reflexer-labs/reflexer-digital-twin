const PIRawGlobalValidator   = artifacts.require("PIRawGlobalValidator");
const PRawGlobalValidator    = artifacts.require("PRawGlobalValidator");
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
  var amountToMint                     = WAD.mul(WAD);
  var treasuryAmount                   = WAD.mul(WAD.div(new BN(2)));
  var treasurySetterTotalAllowance     = WAD.mul(WAD.mul(RAY));
  var treasurySetterPerBlockAllowance  = WAD.mul(WAD.mul(RAY));

  var oracleInitialPrice               = new BN(4.2).mul(WAD);

  // PI Validator
  var Kp                                    = WAD.clone();
  var Ki                                    = WAD.div(new BN("3600"));
  var integralPeriodSize                    = 3600;
  var lowerPrecomputedRateAllowedDeviation  = new BN("990000000000000000");
  var upperPrecomputedRateAllowedDeviation  = new BN("990000000000000000");
  var allowedDeviationIncrease              = RAY;
  var baseUpdateCallerReward                = WAD.clone();
  var maxUpdateCallerReward                 = new BN("30000000000000000000");
  var perSecondCallerRewardIncrease         = new BN("1000002763984612345119745925");
  var perSecondCumulativeLeak               = new BN("999997208243937652252849536"); // 1% per hour
  var noiseBarrier                          = WAD.clone();
  var feedbackOutputUpperBound              = RAY.mul(WAD);
  var feedbackOutputLowerBound              = RAY.mul(new BN(-1)).mul(WAD);
  var integralGranularity                   = 24;
  var minRateTimeline                       = 2592000;

  var initialRedemptionPrice                = new BN(4.2).mul(RAY);

  deployer.deploy(ERC20, tokenSymbol, tokenSymbol).then(function() {
  return deployer.deploy(MockFeed, oracleInitialPrice, true).then(function() {
  return deployer.deploy(MockTreasury, ERC20.address).then(function() {
  return deployer.deploy(MockOracleRelayer, initialRedemptionPrice).then(function() {
  return deployer.deploy(
    PIRawGlobalValidator,
    Kp,
    Ki,
    perSecondCumulativeLeak,
    integralPeriodSize,
    lowerPrecomputedRateAllowedDeviation,
    upperPrecomputedRateAllowedDeviation,
    allowedDeviationIncrease,
    noiseBarrier,
    feedbackOutputUpperBound,
    minRateTimeline,
    feedbackOutputLowerBound,
    [0, 0, 0, 0, 0]
  ).then(function() {
  return deployer.deploy(
    RateSetter,
    MockOracleRelayer.address,
    MockFeed.address,
    MockTreasury.address,
    PIRawGlobalValidator.address,
    baseUpdateCallerReward,
    maxUpdateCallerReward,
    perSecondCallerRewardIncrease,
    integralPeriodSize
  ).then(async function() {
    var token         = await ERC20.deployed();
    var treasury      = await MockTreasury.deployed();
    var validator     = await PIRawGlobalValidator.deployed();
    var rateSetter    = await RateSetter.deployed();
    var oracleRelayer = await MockOracleRelayer.deployed();

    await token.mint(treasury.address, treasuryAmount);

    await treasury.setTotalAllowance(rateSetter.address, treasurySetterTotalAllowance);
    await treasury.setPerBlockAllowance(rateSetter.address, treasurySetterPerBlockAllowance);
  }) }) }) }) }) })
};
