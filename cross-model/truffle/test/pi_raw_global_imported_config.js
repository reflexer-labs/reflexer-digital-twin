const assertFail          = require("./utils/assertFail");
const increaseTime        = require('./utils/increaseTime');
const pidMath             = require('./utils/pidMath');
const logging             = require("./utils/logging");

const BN                  = require('bn.js');
var Decimal               = require('decimal.js');
const fs                  = require('fs');

const PIRawGlobalValidator = artifacts.require("PIRawGlobalValidator");
const RateSetter           = artifacts.require("RateSetter");
const MockOracleRelayer    = artifacts.require("MockOracleRelayer");
const MockTreasury         = artifacts.require("MockTreasury");
const MockFeed             = artifacts.require("MockFeed");
const ERC20                = artifacts.require("ERC20");
const AGUpdater            = artifacts.require("AGUpdater");
const SeedProposerUpdater  = artifacts.require("SeedProposerUpdater");

contract('PIRawGlobalValidator Imported Config', function(accounts) {
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
  var Kp
  var Ki
  var integralPeriodSize                    = 3600;
  var lowerPrecomputedRateAllowedDeviation
  var upperPrecomputedRateAllowedDeviation
  var allowedDeviationIncrease
  var timeWarpedToIncreaseDeviation         = 3600;
  var baseUpdateCallerReward                = WAD.clone();
  var maxUpdateCallerReward                 = new BN("10000000000000000000");
  var perSecondCallerRewardIncrease         = new BN("1000272489688853849040134023"); // 166.666666667% per hour
  var perSecondCumulativeLeak;
  var noiseBarrier;
  var feedbackOutputUpperBound              = RAY.mul(WAD);
  var feedbackOutputLowerBound              = RAY.mul(new BN(-1)).mul(WAD);
  var minRateTimeline;

  var oracleInitialPrice;
  var initialRedemptionPrice;

  var encodedSeedProposer                   = "0x7365656450726f706f7365720000000000000000000000000000000000000000"
  var feeReceiver                           = "0xF320d7Bf928a8eFda0FF624A02e73E9592A03f2B"

  var SPY                                   = 31536000;
  var dataDescription                       = "Market Price (WAD) | Redemption Price (RAY) | Redemption Rate (%) | Per Second Redemption Rate (RAY) | Redemption Rate Timeline (Seconds) | Proportional (No Gain) | Proportional (With Gain) | Integral (No Gain) | Integral (With Gain) | Delay Since Last Update" + "\n"

  // Contracts
  var systemCoin, orcl, treasury, oracleRelayer, validator, rateSetter, agUpdater, seedProposerUpdater;

  // Sim data
  var orclPrices, updateDelays;

  // Logging
  var simDataFilePath;

  // Setup
  beforeEach(async () => {
    await importVariables();

    systemCoin    = await ERC20.new(tokenSymbol, tokenSymbol);
    orcl          = await MockFeed.new(oracleInitialPrice, true);
    treasury      = await MockTreasury.new(systemCoin.address);
    oracleRelayer = await MockOracleRelayer.new(initialRedemptionPrice);
    validator     = await PIRawGlobalValidator.new(
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
    agUpdater           = await AGUpdater.new();
    seedProposerUpdater = await SeedProposerUpdater.new();

    await validator.addAuthority(agUpdater.address);
    await validator.addAuthority(seedProposerUpdater.address);

    await seedProposerUpdater.modifyParameters(validator.address, rateSetter.address);

    await systemCoin.mint(treasury.address, treasuryAmount, {from: accounts[0]});
    await treasury.setTotalAllowance(rateSetter.address, treasurySetterTotalAllowance, {from: accounts[0]});
    await treasury.setPerBlockAllowance(rateSetter.address, treasurySetterPerBlockAllowance, {from: accounts[0]});
  });

  // File I/O
  async function importVariables() {
    let piParams = fs.readFileSync('test/config/pi_global_raw.json');
    piParams = JSON.parse(piParams);

    Kp = new BN(piParams.Kp)
    Ki = new BN(piParams.Ki);
    lowerPrecomputedRateAllowedDeviation = new BN(piParams.lower_precomputed_rate_allowed_deviation);
    upperPrecomputedRateAllowedDeviation = new BN(piParams.upper_precomputed_rate_allowed_deviation);
    allowedDeviationIncrease = new BN(piParams.allowed_deviation_increase);
    noiseBarrier = new BN(piParams.noise_barrier);
    perSecondCumulativeLeak = new BN(piParams.per_second_leak);
    minRateTimeline = piParams.min_rate_timeline;
    oracleInitialPrice = new BN(piParams.oracle_initial_price);
    initialRedemptionPrice = new BN(piParams.initial_redemption_price);
    updateDelays = piParams.delta_t;
    orclPrices = piParams.market_prices;
    simDataFilePath = piParams.save_dir;
  }

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
  });

  it('simulate the raw PI controller using the custom JSON config', async () => {
    if (orclPrices.length != updateDelays.length) {
      console.log("Invalid custom sim array data! Abort");
      return;
    }

    // Logging & data dump
    var printOverview   = false;
    var printStep       = false;

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

    var cumulativeTime;

    for (var i = 0; i < orclPrices.length; i++) {
      marketPrices.push(orclPrices[i]);
      delays.push(updateDelays[i]);
      cumulativeTime += parseInt(updateDelays[i]);

      var update = await executePIUpdate(printStep, parseInt(updateDelays[i]), orclPrices[i].toString())

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
      cumulativeTime.toString(),

      simDataFilePath,
      dataDescription
    );
  })
});
