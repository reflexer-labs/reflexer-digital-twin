const fs = require('fs');

function printSimulationOverview(
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
  totalSecondsPassed
) {
  console.log("Scenario ran over " + totalSecondsPassed.toString() + " seconds" + "\n")
  console.log(dataDescription)

  for (var i = 0; i < marketPrices.length; i++) {
    console.log(
      marketPrices[i] +
      " " +
      redemptionPrices[i] +
      " " +
      globalRedemptionRates[i] +
      " " +
      perSecondRedemptionRates[i] +
      " " +
      redemptionRateTimelines[i] +
      " " +
      proportionalNoGain[i] +
      " " +
      proportionalWithGain[i] +
      " " +
      integralNoGain[i] +
      " " +
      integralWithGain[i] +
      " " +
      delays[i]
    )
  }
}
function printStepUpdate(marketPrice, delay, update) {
  console.log("Contract Derived Per-Second Redemption Rate: " + update.rawContractComputedGlobalRate.toString())
  console.log("Raw Off-Chain Global Computed Redemption Rate: " + update.offChainGlobalRedemptionRate.toString())
  console.log("Market Price: " + marketPrice.toString())
  console.log("Redemption Price: " + update.redemptionPrice.toString())
  console.log("Global Redemption Rate: " + update.globalRedemptionRate.toString())
  console.log("Per Second Redemption Rate (Not Scaled Down): " + update.perSecondRedemptionRate.toString())
  console.log("Redemption Rate Timeline (Seconds): " + update.redemptionRateTimeline.toString())
  console.log("Proportional (No Gain): " + update.proportionalNoGain.toString())
  console.log("Proportional (With Gain): " + update.proportionalWithGain.toString())
  console.log("Integral (No Gain): " + update.integralNoGain.toString())
  console.log("Integral (With Gain): " + update.integralWithGain.toString())
  console.log("Current Fee Receiver System Coin Balance: " + update.feeReceiverBalance.toString())
  console.log("\n")
}

async function saveSimulation(path, content) {
    var bufferedContent = new Buffer(content);

    return new Promise ((resolve, reject) => {
      fs.open(path, 'w', function(err, fd) {
          if (err) {
              reject('Could not open file: ' + err);
          }

          fs.write(fd, bufferedContent, 0, bufferedContent.length, null, function(err) {
              if (err) reject('Error writing to file: ' + err);
              fs.close(fd, function() {
                resolve("OK")
              });
          });
      });
    })
}

async function printAndSaveSimulation(
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
  totalSecondsPassed,

  path,
  dataDescription
) {
  if (printOverview) {
    printSimulationOverview(
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
      totalSecondsPassed
    );
  }

  var simData = "".concat(dataDescription);

  for (var i = 0; i < marketPrices.length; i++) {
    simData = simData.concat(
      marketPrices[i] +
      " " +
      redemptionPrices[i] +
      " " +
      globalRedemptionRates[i] +
      " " +
      perSecondRedemptionRates[i] +
      " " +
      redemptionRateTimelines[i] +
      " " +
      proportionalNoGain[i] +
      " " +
      proportionalWithGain[i] +
      " " +
      integralNoGain[i] +
      " " +
      integralWithGain[i] +
      " " +
      delays[i] +
      "\n"
    )
  }

  await saveSimulation(path, simData);
}

module.exports = {
    printSimulationOverview,
    printStepUpdate,
    saveSimulation,
    printAndSaveSimulation
}
