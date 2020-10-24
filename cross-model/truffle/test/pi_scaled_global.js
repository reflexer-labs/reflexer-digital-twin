const assertFail          = require("./utils/assertFail");
const increaseTime        = require('./utils/increaseTime');
const pidMath             = require('./utils/pidMath');
const logging             = require("./utils/logging");

const BN                  = require('bn.js');
var Decimal               = require('decimal.js');
var Web3                  = require('web3');

const PIScaledGlobalValidator = artifacts.require("PIScaledGlobalValidator");
const RateSetter              = artifacts.require("RateSetter");
const MockOracleRelayer       = artifacts.require("MockOracleRelayer");
const MockTreasury            = artifacts.require("MockTreasury");
const MockFeed                = artifacts.require("MockFeed");
const ERC20                   = artifacts.require("ERC20");
const AGUpdater               = artifacts.require("AGUpdater");
const SeedProposerUpdater     = artifacts.require("SeedProposerUpdater");

contract('PIScaledGlobalValidator', function(accounts) {
  // Default params
  var WAD                              = new BN("1000000000000000000");
  var RAY                              = new BN("1000000000000000000000000000");

  // ERC20
  var tokenSymbol                      = "RAI";

  // Tokens and treasury
  var amountToMint                     = WAD.mul(WAD);
  var treasuryAmount                   = WAD.mul(WAD.div(new BN(2)));
  var treasurySetterTotalAllowance     = WAD.mul(WAD.mul(RAY));
  var treasurySetterPerBlockAllowance  = WAD.mul(WAD.mul(RAY));

  // PI Validator
  var Kp                                    = WAD;
  var Ki                                    = WAD.div(new BN(3600)).div(new BN(3600));
  var integralPeriodSize                    = 3600;
  var lowerPrecomputedRateAllowedDeviation  = new BN("980000000000000000");
  var upperPrecomputedRateAllowedDeviation  = new BN("980000000000000000");
  var allowedDeviationIncrease              = new BN("999970733618363951224236355");  // -10% per hour
  var timeWarpedToIncreaseDeviation         = 3600;
  var baseUpdateCallerReward                = WAD.clone();
  var maxUpdateCallerReward                 = new BN("10000000000000000000");
  var perSecondCallerRewardIncrease         = new BN("1000272489688853849040134023"); // 166.666666667% per hour
  var perSecondCumulativeLeak               = new BN("999970733618363951224236355");  // -10% per hour
  var noiseBarrier                          = new BN("995000000000000000"); // 0.5%
  var feedbackOutputUpperBound              = RAY.mul(WAD);
  var feedbackOutputLowerBound              = RAY.mul(new BN(-1)).mul(WAD);
  var minRateTimeline                       = 2592000;

  var oracleInitialPrice                    = new BN(42).mul(WAD).div(new BN(10)); // WAD
  var initialRedemptionPrice                = new BN(42).mul(RAY).div(new BN(10)); // RAY

  var encodedSeedProposer                   = "0x7365656450726f706f7365720000000000000000000000000000000000000000"
  var feeReceiver                           = "0xF320d7Bf928a8eFda0FF624A02e73E9592A03f2B"

  var SPY                                   = 31536000;
  var dataDescription                       = "Market Price (WAD) | Redemption Price (RAY) | Redemption Rate (%) | Per Second Redemption Rate (RAY) | Redemption Rate Timeline (Seconds) | Proportional (No Gain) | Proportional (With Gain) | Integral (No Gain) | Integral (With Gain) | Delay Since Last Update" + "\n"

  // Contracts
  var systemCoin, orcl, treasury, oracleRelayer, validator, rateSetter, agUpdater, seedProposerUpdater;

  // Web3
  var web3 = new Web3();

  // Setup
  beforeEach(async () => {
    systemCoin    = await ERC20.new(tokenSymbol, tokenSymbol);
    orcl          = await MockFeed.new(oracleInitialPrice, true);
    treasury      = await MockTreasury.new(systemCoin.address);
    oracleRelayer = await MockOracleRelayer.new(initialRedemptionPrice);
    validator     = await PIScaledGlobalValidator.new(
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
    );
    rateSetter    = await RateSetter.new(
      oracleRelayer.address,
      orcl.address,
      treasury.address,
      validator.address,
      baseUpdateCallerReward,
      maxUpdateCallerReward,
      perSecondCallerRewardIncrease,
      integralPeriodSize
    );
    agUpdater     = await AGUpdater.new();
    seedProposerUpdater = await SeedProposerUpdater.new();

    await validator.addAuthority(agUpdater.address);
    await validator.addAuthority(seedProposerUpdater.address);

    await seedProposerUpdater.modifyParameters(validator.address, rateSetter.address);

    await systemCoin.mint(treasury.address, treasuryAmount, {from: accounts[0]});
    await treasury.setTotalAllowance(rateSetter.address, treasurySetterTotalAllowance, {from: accounts[0]});
    await treasury.setPerBlockAllowance(rateSetter.address, treasurySetterPerBlockAllowance, {from: accounts[0]});
  });

  // Feedback loop
  async function updateOnChainRate(pythonRate, bashRate, feeReceiver) {
    try {
      await rateSetter.updateRate(new BN(pythonRate), feeReceiver, {from: accounts[0]});
      return pythonRate;
    } catch(err) {
      try {
        await rateSetter.updateRate(new BN(bashRate), feeReceiver, {from: accounts[0]});
        return bashRate;
      } catch(err) {
        return 0
      }
    }
  }
  async function executePIUpdate(print, randomDelay, randomPrice) {
    await increaseTime.advanceTime(randomDelay);

    // Set the new oracle price
    await orcl.updateTokenPrice(randomPrice, {from: accounts[0]});

    // Get the redemption price
    var latestRedemptionPrice = (await oracleRelayer.redemptionPrice.call()).toString();

    // Get the next per-second rate
    var pscl = (await validator.pscl.call()).toString();
    var tlv = (await validator.tlv.call()).toString();
    var iapcr = (await rateSetter.rpower.call(pscl, tlv, RAY.toString(10))).toString();
    var nextRateData = (await validator.getNextRedemptionRate.call(randomPrice, latestRedemptionPrice, iapcr))

    var newPerSecondRate;
    var newBashCalculatedPerSecondRate;
    var newPythonCalculatedPerSecondRate;
    var normalizedGlobalRate;

    if (nextRateData[0].eq(RAY)) {
      newBashCalculatedPerSecondRate = RAY.toString(10)
      newPythonCalculatedPerSecondRate = RAY.toString(10);
      normalizedGlobalRate = "0"
    } else {
      normalizedGlobalRate = nextRateData[0].sub(RAY).divmod(new BN("10000000000000000000000000"));

      if (normalizedGlobalRate.div.toString(10) == "0" && normalizedGlobalRate.mod.isNeg()) {
        normalizedGlobalRate = "-".concat(normalizedGlobalRate.div.toString(10) + "." + normalizedGlobalRate.mod.abs().toString(10));
      } else {
        normalizedGlobalRate = normalizedGlobalRate.div.toString(10) + "." + normalizedGlobalRate.mod.abs().toString(10);
      }

      newBashCalculatedPerSecondRate = await pidMath.bashComputePerSecondRate(normalizedGlobalRate, nextRateData[3].toString(10));
      newPythonCalculatedPerSecondRate = await pidMath.pythonComputePerSecondRate(normalizedGlobalRate, nextRateData[3].toString(10));
    }

    var normalizedMarketPrice = new BN(randomPrice).divmod(WAD);
    var gainAdjustedTerms = await validator.getGainAdjustedTerms(nextRateData[1].toString(10), nextRateData[2].toString(10), {from: accounts[0]});

    if (print) {
      var offChainPythonRedemptionRate = (await rateSetter.rpower.call(newPythonCalculatedPerSecondRate.toString(), nextRateData[3].toString(10), RAY.toString(10))).toString();
      var offChainBashRedemptionRate   = (await rateSetter.rpower.call(newBashCalculatedPerSecondRate.toString(), nextRateData[3].toString(10), RAY.toString(10))).toString();

      console.log("Python Computed Global Rate: " + newPythonCalculatedPerSecondRate.toString())
      console.log("Bash Computed Global Rate: " + newBashCalculatedPerSecondRate.toString())
      console.log("Contract Derived Per-Second Redemption Rate: " + nextRateData[0].toString(10))
      console.log("Python Computed Per-Second Redemption Rate: " + offChainPythonRedemptionRate)
      console.log("Bash Computed Per-Second Redemption Rate: " + offChainBashRedemptionRate)
      console.log("Market Price: " + randomPrice.toString(10))
      console.log("Redemption Price: " + latestRedemptionPrice)
      console.log("Global Redemption Rate: " + normalizedGlobalRate)
      console.log("Redemption Rate Timeline (Seconds): " + nextRateData[3].toString(10))
    }

    // Update the rate on-chain
    newPerSecondRate = await updateOnChainRate(newPythonCalculatedPerSecondRate, newBashCalculatedPerSecondRate, feeReceiver)
    if (newPerSecondRate.toString() == "0") {
      normalizedGlobalRate = Math.ceil(parseFloat(normalizedGlobalRate));

      newBashCalculatedPerSecondRate   = await pidMath.bashComputePerSecondRate(normalizedGlobalRate, nextRateData[3].toString(10));
      newPythonCalculatedPerSecondRate = await pidMath.pythonComputePerSecondRate(normalizedGlobalRate, nextRateData[3].toString(10));

      offChainPythonRedemptionRate = (await rateSetter.rpower.call(newPythonCalculatedPerSecondRate.toString(), nextRateData[3].toString(10), RAY.toString(10))).toString();
      offChainBashRedemptionRate   = (await rateSetter.rpower.call(newBashCalculatedPerSecondRate.toString(), nextRateData[3].toString(10), RAY.toString(10))).toString();

      console.log("Global Trimmed Redemption Rate: " + normalizedGlobalRate)
      console.log("Python Computed Per-Second Redemption Rate (Trimmed): " + offChainPythonRedemptionRate)
      console.log("Bash Computed Per-Second Redemption Rate (Trimmed): " + offChainBashRedemptionRate)

      newPerSecondRate = await updateOnChainRate(newPythonCalculatedPerSecondRate, newBashCalculatedPerSecondRate, feeReceiver)
    }

    // Throw if the rate has been updated
    if (newPerSecondRate.toString() == "0") {
      throw 'Cannot update the redemption rate given the current allowed deviation!';
    }

    // Get the global off-chain computed redemption rate
    var offChainGlobalRedemptionRate = (await rateSetter.rpower.call(newPerSecondRate, nextRateData[3].toString(10), RAY.toString(10))).toString();

    // Get and store the receiver system coin balance
    var currentReceiverBalance = (await systemCoin.balanceOf.call(feeReceiver)).toString()
    var adjustedReceiverBalance = new BN(currentReceiverBalance).divmod(WAD)
    adjustedReceiverBalance = adjustedReceiverBalance.div.toString(10) + "." + adjustedReceiverBalance.mod.abs().toString(10)

    if (print) {
      console.log("Per Second Redemption Rate (Not Scaled Down): " + newPerSecondRate)
      console.log("Proportional (No Gain): " + nextRateData[1].toString(10))
      console.log("Proportional (With Gain): " + gainAdjustedTerms[0].toString(10))
      console.log("Integral (No Gain): " + nextRateData[2].toString(10))
      console.log("Integral (With Gain): " + gainAdjustedTerms[1].toString(10))
      console.log("Current Fee Receiver System Coin Balance: " + adjustedReceiverBalance)
      console.log("\n")
    }

    return {
      rawContractComputedGlobalRate: nextRateData[0].toString(10),
      offChainGlobalRedemptionRate: offChainGlobalRedemptionRate,
      redemptionPrice: latestRedemptionPrice,
      globalRedemptionRate: normalizedGlobalRate,
      perSecondRedemptionRate: newPerSecondRate,
      redemptionRateTimeline: nextRateData[3].toString(10),
      proportionalNoGain: nextRateData[1].toString(10),
      proportionalWithGain: gainAdjustedTerms[0].toString(10),
      integralNoGain: nextRateData[2].toString(10),
      integralWithGain: gainAdjustedTerms[1].toString(10),
      feeReceiverBalance: adjustedReceiverBalance
    }
  }

  // Tests
  it('should check that the deployment was successful', async () => {
    const setRedemptionPrice = (await oracleRelayer.redemptionPrice.call()).toString();
    assert.equal(setRedemptionPrice, initialRedemptionPrice.toString(10))

    const orclPrice = (await orcl.read.call());

    assert.equal(orclPrice.toString(10), oracleInitialPrice.toString(10));
  })

  it('should check that the PID math works correctly', async () => {
    var perSecondRate = await pidMath.bashComputePerSecondRate("50", "100000");
    assert.equal(perSecondRate.toString(), "1000004054659301190448365314");
  })

  it('should get the next rate when prices are equal, this is the first update and there was no warp', async () => {
    var pscl = (await validator.pscl.call()).toString();
    var tlv = (await validator.tlv.call()).toString();
    var iapcr = (await rateSetter.rpower.call(pscl, tlv, RAY.toString(10))).toString();

    var nextRateData = (await validator.getNextRedemptionRate.call(oracleInitialPrice.toString(10), initialRedemptionPrice.toString(10), iapcr))
    assert.equal(nextRateData[0].toString(10), RAY.toString(10));
    assert.equal(nextRateData[1].toString(10), "0");
    assert.equal(nextRateData[2].toString(10), "0");
    assert.equal(nextRateData[3].toString(10), "31536000");
  })

  it('should get the next rate when prices are equal, this is the first update and there was a single warp', async () => {
    await increaseTime.advanceTime(60*60*6);

    var pscl = (await validator.pscl.call()).toString();
    var tlv = (await validator.tlv.call()).toString();
    var iapcr = (await rateSetter.rpower.call(pscl, tlv, RAY.toString(10))).toString();

    var nextRateData = (await validator.getNextRedemptionRate.call(oracleInitialPrice.toString(10), initialRedemptionPrice.toString(10), iapcr))
    assert.equal(nextRateData[0].toString(10), RAY.toString(10));
    assert.equal(nextRateData[1].toString(10), "0");
    assert.equal(nextRateData[2].toString(10), "0");
    assert.equal(nextRateData[3].toString(10), "31536000");
  })

  it('should simulate a huge positive shock and then a comeback to the redemption price', async () => {
    var shockPrice = new BN(65).mul(WAD).div(new BN(10));
    var shockSteps = 5;
    var stepsPostShock = 24;

    // Logging & data dump
    var printOverview   = false;
    var printStep       = false;
    var simDataFilePath = "test/saved_sims/pi_global/scaled/big_positive_shock.txt";

    // First market price == redemption price
    var marketPrices = [oracleInitialPrice.toString(10)];
    var redemptionPrices = [initialRedemptionPrice.toString(10)];
    var globalRedemptionRates = ["0"];
    var offChainGlobalRedemptionRates = [RAY.toString(10)];
    var perSecondRedemptionRates = [RAY.toString(10)];
    var feeReceiverBalances = [];
    var redemptionRateTimelines = [SPY.toString(10)];
    var proportionalNoGain = ["0"];
    var delays = [integralPeriodSize.toString()];
    var proportionalWithGain = ["0"];
    var integralNoGain = ["0"];
    var integralWithGain = ["0"];

    await increaseTime.advanceTime(integralPeriodSize);
    await rateSetter.updateRate(RAY.toString(10), feeReceiver, {from: accounts[0]});

    var currentReceiverBalance = (await systemCoin.balanceOf.call(feeReceiver)).toString()
    var adjustedReceiverBalance = new BN(currentReceiverBalance).divmod(WAD)
    adjustedReceiverBalance = adjustedReceiverBalance.div.toString(10) + "." + adjustedReceiverBalance.mod.abs().toString(10)
    feeReceiverBalances.push(adjustedReceiverBalance)

    if (printStep) {
      var firstUpdate = {
        rawContractComputedGlobalRate: RAY.toString(10),
        offChainGlobalRedemptionRate: RAY.toString(10),
        redemptionPrice: initialRedemptionPrice.toString(10),
        globalRedemptionRate: RAY.toString(10),
        perSecondRedemptionRate: RAY.toString(10),
        redemptionRateTimeline: SPY,
        proportionalNoGain: "0",
        proportionalWithGain: "0",
        integralNoGain: "0",
        integralWithGain: "0",
        feeReceiverBalance: adjustedReceiverBalance
      }
      logging.printStepUpdate(
        oracleInitialPrice.toString(10),
        integralPeriodSize,
        firstUpdate
      );
    }

    // Simulate the positive shock
    var update;

    for (var i = 0; i < shockSteps; i++) {
      marketPrices.push(shockPrice.toString(10));
      delays.push(integralPeriodSize);
      update = await executePIUpdate(printStep, integralPeriodSize, shockPrice.toString(10))

      redemptionPrices.push(update.redemptionPrice);
      globalRedemptionRates.push(update.globalRedemptionRate);
      offChainGlobalRedemptionRates.push(update.offChainGlobalRedemptionRate);
      perSecondRedemptionRates.push(update.perSecondRedemptionRate);
      feeReceiverBalances.push(update.feeReceiverBalance);
      redemptionRateTimelines.push(update.redemptionRateTimeline);
      proportionalNoGain.push(update.proportionalNoGain);
      proportionalWithGain.push(update.proportionalWithGain);
      integralNoGain.push(update.integralNoGain);
      integralWithGain.push(update.integralWithGain);
    }

    // Then bring the market price back to redemption
    for (var i = 0; i < stepsPostShock; i++) {
      var newMarketPrice = new BN((await oracleRelayer.redemptionPrice.call()).toString()).div(new BN("1000000000"));
      newMarketPrice = newMarketPrice.toString(10);

      marketPrices.push(newMarketPrice);
      delays.push(integralPeriodSize);
      update = await executePIUpdate(printStep, integralPeriodSize, newMarketPrice)

      redemptionPrices.push(update.redemptionPrice);
      globalRedemptionRates.push(update.globalRedemptionRate);
      offChainGlobalRedemptionRates.push(update.offChainGlobalRedemptionRate);
      perSecondRedemptionRates.push(update.perSecondRedemptionRate);
      feeReceiverBalances.push(update.feeReceiverBalance);
      redemptionRateTimelines.push(update.redemptionRateTimeline);
      proportionalNoGain.push(update.proportionalNoGain);
      proportionalWithGain.push(update.proportionalWithGain);
      integralNoGain.push(update.integralNoGain);
      integralWithGain.push(update.integralWithGain);
    }

    await logging.printAndSaveSimulation(
      printOverview,

      marketPrices,
      redemptionPrices,
      globalRedemptionRates,
      perSecondRedemptionRates,
      redemptionRateTimelines,
      proportionalNoGain,
      proportionalWithGain,
      integralNoGain,
      integralWithGain,
      delays,
      (integralPeriodSize * (shockSteps + stepsPostShock + 1)).toString(),

      simDataFilePath,
      dataDescription
    );
  })

  it('should simulate a huge negative shock and then a comeback to the redemption price', async () => {
    var shockPrice = new BN(25).mul(WAD).div(new BN(10));
    var shockSteps = 5;
    var stepsPostShock = 24;

    // Logging & data dump
    var printOverview   = false;
    var printStep       = false;
    var simDataFilePath = "test/saved_sims/pi_global/scaled/big_negative_shock.txt";

    // First market price == redemption price
    var marketPrices = [oracleInitialPrice.toString(10)];
    var redemptionPrices = [initialRedemptionPrice.toString(10)];
    var globalRedemptionRates = ["0"];
    var offChainGlobalRedemptionRates = [RAY.toString(10)];
    var perSecondRedemptionRates = [RAY.toString(10)];
    var feeReceiverBalances = [];
    var redemptionRateTimelines = [SPY.toString(10)];
    var proportionalNoGain = ["0"];
    var delays = [integralPeriodSize.toString()];
    var proportionalWithGain = ["0"];
    var integralNoGain = ["0"];
    var integralWithGain = ["0"];

    await increaseTime.advanceTime(integralPeriodSize);
    await rateSetter.updateRate(RAY.toString(10), feeReceiver, {from: accounts[0]});

    var currentReceiverBalance = (await systemCoin.balanceOf.call(feeReceiver)).toString()
    var adjustedReceiverBalance = new BN(currentReceiverBalance).divmod(WAD)
    adjustedReceiverBalance = adjustedReceiverBalance.div.toString(10) + "." + adjustedReceiverBalance.mod.abs().toString(10)
    feeReceiverBalances.push(adjustedReceiverBalance)

    if (printStep) {
      var firstUpdate = {
        rawContractComputedGlobalRate: RAY.toString(10),
        offChainGlobalRedemptionRate: RAY.toString(10),
        redemptionPrice: initialRedemptionPrice.toString(10),
        globalRedemptionRate: RAY.toString(10),
        perSecondRedemptionRate: RAY.toString(10),
        redemptionRateTimeline: SPY,
        proportionalNoGain: "0",
        proportionalWithGain: "0",
        integralNoGain: "0",
        integralWithGain: "0",
        feeReceiverBalance: adjustedReceiverBalance
      }
      logging.printStepUpdate(
        oracleInitialPrice.toString(10),
        integralPeriodSize,
        firstUpdate
      );
    }

    // Simulate the positive shock
    var update;

    for (var i = 0; i < shockSteps; i++) {
      marketPrices.push(shockPrice.toString(10));
      delays.push(integralPeriodSize);
      update = await executePIUpdate(printStep, integralPeriodSize, shockPrice.toString(10))

      redemptionPrices.push(update.redemptionPrice);
      globalRedemptionRates.push(update.globalRedemptionRate);
      offChainGlobalRedemptionRates.push(update.offChainGlobalRedemptionRate);
      perSecondRedemptionRates.push(update.perSecondRedemptionRate);
      feeReceiverBalances.push(update.feeReceiverBalance);
      redemptionRateTimelines.push(update.redemptionRateTimeline);
      proportionalNoGain.push(update.proportionalNoGain);
      proportionalWithGain.push(update.proportionalWithGain);
      integralNoGain.push(update.integralNoGain);
      integralWithGain.push(update.integralWithGain);
    }

    // Then bring the market price back to redemption
    for (var i = 0; i < stepsPostShock; i++) {
      var newMarketPrice = new BN((await oracleRelayer.redemptionPrice.call()).toString()).div(new BN("1000000000"));
      newMarketPrice = newMarketPrice.toString(10);

      marketPrices.push(newMarketPrice.toString(10));
      delays.push(integralPeriodSize);
      update = await executePIUpdate(printStep, integralPeriodSize, newMarketPrice)

      redemptionPrices.push(update.redemptionPrice);
      globalRedemptionRates.push(update.globalRedemptionRate);
      offChainGlobalRedemptionRates.push(update.offChainGlobalRedemptionRate);
      perSecondRedemptionRates.push(update.perSecondRedemptionRate);
      feeReceiverBalances.push(update.feeReceiverBalance);
      redemptionRateTimelines.push(update.redemptionRateTimeline);
      proportionalNoGain.push(update.proportionalNoGain);
      proportionalWithGain.push(update.proportionalWithGain);
      integralNoGain.push(update.integralNoGain);
      integralWithGain.push(update.integralWithGain);
    }

    await logging.printAndSaveSimulation(
      printOverview,

      marketPrices,
      redemptionPrices,
      globalRedemptionRates,
      perSecondRedemptionRates,
      redemptionRateTimelines,
      proportionalNoGain,
      proportionalWithGain,
      integralNoGain,
      integralWithGain,
      delays,
      (integralPeriodSize * (shockSteps + stepsPostShock + 1)).toString(),

      simDataFilePath,
      dataDescription
    );
  })

  it("should do a positive step change in the market price over one year (with compounding)", async () => {
    // Nullify the integral (set Ki to zero) so we get a clean and valid result
    await agUpdater.modifyParameters(validator.address, 0);

    // Params
    var loops = 200;
    var orclPrice = new BN(462).mul(WAD).div(new BN(100)).toString(10); // 10% market price positive deviation

    // Logging & data dump
    var printOverview   = false;
    var printStep       = false;
    var simDataFilePath = "test/saved_sims/pi_global/scaled/one_year_positive_step_change_with_compounding.txt";

    // Data arrays
    var marketPrices = [];
    var redemptionPrices = [];
    var globalRedemptionRates = [];
    var offChainGlobalRedemptionRates = [];
    var perSecondRedemptionRates = [];
    var feeReceiverBalances = [];
    var redemptionRateTimelines = [];
    var proportionalNoGain = [];
    var delays = [];
    var proportionalWithGain = [];
    var integralNoGain = [];
    var integralWithGain = [];

    // Initial update
    var update;
    for (var i = 0; i < loops; i++) {
      update = await executePIUpdate(printStep, SPY / loops, orclPrice)
      marketPrices.push(orclPrice)
      redemptionPrices.push(update.redemptionPrice);
      globalRedemptionRates.push(update.globalRedemptionRate);
      offChainGlobalRedemptionRates.push(update.offChainGlobalRedemptionRate);
      perSecondRedemptionRates.push(update.perSecondRedemptionRate);
      feeReceiverBalances.push(update.feeReceiverBalance);
      redemptionRateTimelines.push(update.redemptionRateTimeline);
      proportionalNoGain.push(update.proportionalNoGain);
      proportionalWithGain.push(update.proportionalWithGain);
      integralNoGain.push(update.integralNoGain);
      integralWithGain.push(update.integralWithGain);
    }

    // Market comes close to redemption
    orclPrice = new BN((await oracleRelayer.redemptionPrice.call()).toString()).div(new BN("1000000000"));;
    update = await executePIUpdate(printStep, integralPeriodSize, orclPrice)

    marketPrices.push(orclPrice)
    redemptionPrices.push(update.redemptionPrice);
    globalRedemptionRates.push(update.globalRedemptionRate);
    offChainGlobalRedemptionRates.push(update.offChainGlobalRedemptionRate);
    perSecondRedemptionRates.push(update.perSecondRedemptionRate);
    feeReceiverBalances.push(update.feeReceiverBalance);
    redemptionRateTimelines.push(update.redemptionRateTimeline);
    proportionalNoGain.push(update.proportionalNoGain);
    proportionalWithGain.push(update.proportionalWithGain);
    integralNoGain.push(update.integralNoGain);
    integralWithGain.push(update.integralWithGain);

    await logging.printAndSaveSimulation(
      printOverview,

      marketPrices,
      redemptionPrices,
      globalRedemptionRates,
      perSecondRedemptionRates,
      redemptionRateTimelines,
      proportionalNoGain,
      proportionalWithGain,
      integralNoGain,
      integralWithGain,
      delays,
      (SPY + integralPeriodSize).toString(),

      simDataFilePath,
      dataDescription
    );
  })

  it("should do a negative step change in the market price over one year (with compounding)", async () => {
    // Nullify the integral (set Ki to zero) so we get a clean and valid result
    await agUpdater.modifyParameters(validator.address, 0);

    // Params
    var loops = 200;
    var orclPrice = new BN(378).mul(WAD).div(new BN(100)).toString(10); // -10% market price positive deviation

    // Logging & data dump
    var printOverview   = false;
    var printStep       = false;
    var simDataFilePath = "test/saved_sims/pi_global/scaled/one_year_negative_step_change_with_compounding.txt";

    // Data arrays
    var marketPrices = [];
    var redemptionPrices = [];
    var globalRedemptionRates = [];
    var offChainGlobalRedemptionRates = [];
    var perSecondRedemptionRates = [];
    var feeReceiverBalances = [];
    var redemptionRateTimelines = [];
    var proportionalNoGain = [];
    var delays = [];
    var proportionalWithGain = [];
    var integralNoGain = [];
    var integralWithGain = [];

    // Initial update
    for (var i = 0; i < loops; i++) {
      var update = await executePIUpdate(printStep, SPY / loops, orclPrice)
      redemptionPrices.push(update.redemptionPrice);
      globalRedemptionRates.push(update.globalRedemptionRate);
      offChainGlobalRedemptionRates.push(update.offChainGlobalRedemptionRate);
      perSecondRedemptionRates.push(update.perSecondRedemptionRate);
      feeReceiverBalances.push(update.feeReceiverBalance);
      redemptionRateTimelines.push(update.redemptionRateTimeline);
      proportionalNoGain.push(update.proportionalNoGain);
      proportionalWithGain.push(update.proportionalWithGain);
      integralNoGain.push(update.integralNoGain);
      integralWithGain.push(update.integralWithGain);
    }

    // Market comes close to redemption
    orclPrice = new BN((await oracleRelayer.redemptionPrice.call()).toString()).div(new BN("1000000000"));;
    update = await executePIUpdate(printStep, integralPeriodSize, orclPrice)
    redemptionPrices.push(update.redemptionPrice);
    globalRedemptionRates.push(update.globalRedemptionRate);
    offChainGlobalRedemptionRates.push(update.offChainGlobalRedemptionRate);
    perSecondRedemptionRates.push(update.perSecondRedemptionRate);
    feeReceiverBalances.push(update.feeReceiverBalance);
    redemptionRateTimelines.push(update.redemptionRateTimeline);
    proportionalNoGain.push(update.proportionalNoGain);
    proportionalWithGain.push(update.proportionalWithGain);
    integralNoGain.push(update.integralNoGain);
    integralWithGain.push(update.integralWithGain);

    await logging.printAndSaveSimulation(
      printOverview,

      marketPrices,
      redemptionPrices,
      globalRedemptionRates,
      perSecondRedemptionRates,
      redemptionRateTimelines,
      proportionalNoGain,
      proportionalWithGain,
      integralNoGain,
      integralWithGain,
      delays,
      (SPY + integralPeriodSize).toString(),

      simDataFilePath,
      dataDescription
    );
  })

  it('should simulate the PI global scaled validator using a predefined scenario', async () => {
    // Local simulation predefined scenario
    var orclPrices = [
      "4200000000000000000",
      "4300000000000000000",
      "4300000000000000000",
      "4300000000000000000",
      "4200000000000000000",
      "4200000000000000000",
      "4200000000000000000",
      "4200000000000000000",
      "4100000000000000000",
      "4100000000000000000",
      "4100000000000000000",
      "4100000000000000000",
      "4200000000000000000",
      "4200000000000000000",
      "4200000000000000000",
      "4200000000000000000",
      "4200000000000000000",
      "4200000000000000000",
      "4200000000000000000",
      "4200000000000000000",
      "4199260881094347634",
      "4199260881094347634",
      "4199260881094347634"
    ];

    // Logging & data dump
    var printOverview   = false;
    var printStep       = false;
    var simDataFilePath = "test/saved_sims/pi_global/scaled/predefined_scenario.txt";

    // Data arrays
    var marketPrices = [];
    var redemptionPrices = [];
    var globalRedemptionRates = [];
    var offChainGlobalRedemptionRates = [];
    var perSecondRedemptionRates = [];
    var feeReceiverBalances = [];
    var redemptionRateTimelines = [];
    var proportionalNoGain = [];
    var delays = [];
    var proportionalWithGain = [];
    var integralNoGain = [];
    var integralWithGain = [];

    for (var i = 0; i < orclPrices.length; i++) {
      marketPrices.push(orclPrices[i].toString(10));
      delays.push(integralPeriodSize);

      var update = await executePIUpdate(printStep, integralPeriodSize, orclPrices[i])

      redemptionPrices.push(update.redemptionPrice);
      globalRedemptionRates.push(update.globalRedemptionRate);
      offChainGlobalRedemptionRates.push(update.offChainGlobalRedemptionRate);
      perSecondRedemptionRates.push(update.perSecondRedemptionRate);
      feeReceiverBalances.push(update.feeReceiverBalance);
      redemptionRateTimelines.push(update.redemptionRateTimeline);
      proportionalNoGain.push(update.proportionalNoGain);
      proportionalWithGain.push(update.proportionalWithGain);
      integralNoGain.push(update.integralNoGain);
      integralWithGain.push(update.integralWithGain);
    }

    await logging.printAndSaveSimulation(
      printOverview,

      marketPrices,
      redemptionPrices,
      globalRedemptionRates,
      perSecondRedemptionRates,
      redemptionRateTimelines,
      proportionalNoGain,
      proportionalWithGain,
      integralNoGain,
      integralWithGain,
      delays,
      (integralPeriodSize * orclPrices.length).toString(),

      simDataFilePath,
      dataDescription
    );
  });

  it('should simulate the PI global scaled validator using randomly generated prices and delays', async () => {
    // Params
    var priceLowerBound = 3.8;
    var priceUpperBound = 4.6;
    var delayLowerBound = integralPeriodSize;
    var delayUpperBound = integralPeriodSize * 8;
    var steps           = 10;

    // Logging & data dump
    var printOverview   = false;
    var printStep       = false;
    var simDataFilePath = "test/saved_sims/pi_global/scaled/randomly_generated_prices_and_delays.txt";

    // Logic
    var marketPrices = [];
    var redemptionPrices = [];
    var globalRedemptionRates = [];
    var offChainGlobalRedemptionRates = [];
    var perSecondRedemptionRates = [];
    var feeReceiverBalances = [];
    var redemptionRateTimelines = [];
    var proportionalNoGain = [];
    var delays = [];
    var proportionalWithGain = [];
    var integralNoGain = [];
    var integralWithGain = [];

    var accumulatedDelay = 0;

    for (var i = 0; i < steps; i++) {
      var randomPrice = (Math.random() * (priceUpperBound - priceLowerBound) + priceLowerBound).toFixed(18)
      randomPrice = randomPrice.toString().replace(".", "");
      marketPrices.push(randomPrice);

      var randomDelay = Math.floor(Math.random() * (delayUpperBound - delayLowerBound + 1) + delayLowerBound);
      accumulatedDelay += randomDelay;

      delays.push(randomDelay);

      var update = await executePIUpdate(printStep, randomDelay, randomPrice)

      redemptionPrices.push(update.redemptionPrice);
      globalRedemptionRates.push(update.globalRedemptionRate);
      offChainGlobalRedemptionRates.push(update.offChainGlobalRedemptionRate);
      perSecondRedemptionRates.push(update.perSecondRedemptionRate);
      feeReceiverBalances.push(update.feeReceiverBalance);
      redemptionRateTimelines.push(update.redemptionRateTimeline);
      proportionalNoGain.push(update.proportionalNoGain);
      proportionalWithGain.push(update.proportionalWithGain);
      integralNoGain.push(update.integralNoGain);
      integralWithGain.push(update.integralWithGain);
    }
    await logging.printAndSaveSimulation(
      printOverview,

      marketPrices,
      redemptionPrices,
      globalRedemptionRates,
      perSecondRedemptionRates,
      redemptionRateTimelines,
      proportionalNoGain,
      proportionalWithGain,
      integralNoGain,
      integralWithGain,
      delays,
      accumulatedDelay.toString(),

      simDataFilePath,
      dataDescription
    );
  });
});
