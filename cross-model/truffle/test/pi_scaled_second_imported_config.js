const assertFail          = require("./utils/assertFail");
const increaseTime        = require('./utils/increaseTime');
const pidMath             = require('./utils/pidMath');
const logging             = require("./utils/logging");

const BN                  = require('bn.js');
var Decimal               = require('decimal.js');
const fs                  = require('fs');

const PIScaledPerSecondCalculator = artifacts.require("PIScaledPerSecondCalculator");
const RateSetter                  = artifacts.require("RateSetter");
const MockOracleRelayer           = artifacts.require("MockOracleRelayer");
const MockTreasury                = artifacts.require("MockTreasury");
const MockFeed                    = artifacts.require("MockFeed");
const ERC20                       = artifacts.require("ERC20");
const AGUpdater                   = artifacts.require("AGUpdater");
const SeedProposerUpdater         = artifacts.require("SeedProposerUpdater");

contract('PIScaledPerSecondCalculator Imported Config', function(accounts) {
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

  // PI Calculator
  var Kp
  var Ki
  var integralPeriodSize                    = 3600;
  var timeWarpedToIncreaseDeviation         = 3600;
  var baseUpdateCallerReward                = WAD.clone();
  var maxUpdateCallerReward                 = new BN("10000000000000000000");
  var perSecondCallerRewardIncrease         = new BN("1000272489688853849040134023"); // 166.666666667% per hour
  var perSecondCumulativeLeak;
  var noiseBarrier;
  var feedbackOutputUpperBound              = RAY.mul(WAD);
  var feedbackOutputLowerBound              = RAY.sub(new BN("1")).mul(new BN("-1"));
  var minRateTimeline;

  var oracleInitialPrice;
  var initialRedemptionPrice;

  var encodedSeedProposer                   = "0x7365656450726f706f736572"
  var feeReceiver                           = "0xF320d7Bf928a8eFda0FF624A02e73E9592A03f2B"

  var dataDescription                       = "Market Price (WAD) | Redemption Price (RAY) | Redemption Rate (%) | Per Second Redemption Rate (RAY) | Redemption Rate Timeline (Seconds) | Proportional (No Gain) | Proportional (With Gain) | Integral (No Gain) | Integral (With Gain) | Delay Since Last Update" + "\n"

  // Contracts
  var systemCoin, orcl, treasury, oracleRelayer, calculator, rateSetter, agUpdater, seedProposerUpdater;

  // Setup
  beforeEach(async () => {
    await importVariables();

    systemCoin    = await ERC20.new(tokenSymbol, tokenSymbol);
    orcl          = await MockFeed.new(oracleInitialPrice, true);
    treasury      = await MockTreasury.new(systemCoin.address);
    oracleRelayer = await MockOracleRelayer.new(initialRedemptionPrice);
    calculator     = await PIScaledPerSecondCalculator.new(
      Kp,
      Ki,
      perSecondCumulativeLeak,
      integralPeriodSize,
      noiseBarrier,
      feedbackOutputUpperBound,
      feedbackOutputLowerBound,
      [0, 0, 0, 0, 0]
    );
    rateSetter    = await RateSetter.new(
      oracleRelayer.address,
      orcl.address,
      treasury.address,
      calculator.address,
      baseUpdateCallerReward,
      maxUpdateCallerReward,
      perSecondCallerRewardIncrease,
      integralPeriodSize
    );
    agUpdater           = await AGUpdater.new();
    seedProposerUpdater = await SeedProposerUpdater.new();

    await calculator.addAuthority(agUpdater.address);
    await calculator.addAuthority(seedProposerUpdater.address);

    await seedProposerUpdater.modifyParameters(calculator.address, rateSetter.address);

    await systemCoin.mint(treasury.address, treasuryAmount, {from: accounts[0]});
    await treasury.setTotalAllowance(rateSetter.address, treasurySetterTotalAllowance, {from: accounts[0]});
    await treasury.setPerBlockAllowance(rateSetter.address, treasurySetterPerBlockAllowance, {from: accounts[0]});
  });

  // File I/O
  async function importVariables() {
    let piParams = fs.readFileSync('test/config/pi_second_scaled.json');
    piParams = JSON.parse(piParams);

    Kp = new BN(piParams.Kp)
    Ki = new BN(piParams.Ki);
    noiseBarrier = new BN(piParams.noise_barrier);
    perSecondCumulativeLeak = new BN(piParams.per_second_leak);
    oracleInitialPrice = new BN(piParams.oracle_initial_price);
    initialRedemptionPrice = new BN(piParams.initial_redemption_price);
    updateDelays = piParams.delta_t;
    orclPrices = piParams.market_prices;
    simDataFilePath = piParams.save_dir;
  }

  // Feedback loop
  async function updateOnChainRate(feeReceiver) {
    await rateSetter.updateRate(feeReceiver, {from: accounts[0]});
  }
  async function executePIUpdate(print, randomDelay, randomPrice) {
    await increaseTime.advanceTime(randomDelay);

    // Set the new oracle price
    await orcl.updateTokenPrice(randomPrice, {from: accounts[0]});

    // Get the redemption price
    var latestRedemptionPrice = (await oracleRelayer.redemptionPrice.call()).toString();

    // Get the next per-second rate
    var pscl = (await calculator.pscl.call()).toString();
    var tlv = (await calculator.tlv.call()).toString();
    var iapcr = (await rateSetter.rpower.call(pscl, tlv, RAY.toString(10))).toString();
    var nextRateData = (await calculator.getNextRedemptionRate.call(randomPrice, latestRedemptionPrice, iapcr))

    var gainAdjustedTerms = await calculator.getGainAdjustedTerms(nextRateData[1], nextRateData[2], {from: accounts[0]});

    if (print) {
      console.log("Contract Computed Per-Second Redemption Rate: " + nextRateData[0].toString(10))
      console.log("Market Price: " + randomPrice.toString(10))
      console.log("Redemption Price: " + latestRedemptionPrice)
      console.log("Redemption Rate Timeline (Seconds): " + nextRateData[3].toString(10))
    }

    // Update the rate on-chain
    await updateOnChainRate(feeReceiver)

    // Get and store the receiver system coin balance
    var currentReceiverBalance = (await systemCoin.balanceOf.call(feeReceiver)).toString()
    var adjustedReceiverBalance = new BN(currentReceiverBalance).divmod(WAD)
    adjustedReceiverBalance = adjustedReceiverBalance.div.toString(10) + "." + adjustedReceiverBalance.mod.abs().toString(10)

    if (print) {
      console.log("Proportional (No Gain): " + nextRateData[1].toString(10))
      console.log("Proportional (With Gain): " + gainAdjustedTerms[0].toString(10))
      console.log("Integral (No Gain): " + nextRateData[2].toString(10))
      console.log("Integral (With Gain): " + gainAdjustedTerms[1].toString(10))
      console.log("Current Fee Receiver System Coin Balance: " + adjustedReceiverBalance)
      console.log("\n")
    }

    return {
      contractComputedPerSecondRate: nextRateData[0].toString(10),
      redemptionPrice: latestRedemptionPrice,
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
  it('simulate the scaled per-second PI controller using the custom JSON config', async () => {
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
      globalRedemptionRates.push("1");
      perSecondRedemptionRates.push(update.contractComputedPerSecondRate);
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
