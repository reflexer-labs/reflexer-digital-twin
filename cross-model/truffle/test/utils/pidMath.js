var exec      = require('shelljs.exec')
const spawn   = require("child_process").spawn;

async function bashComputePerSecondRate(globalRate, rateTimeline) {
  var result = exec('./test/utils/rate_calculation/computePerSecondRate.sh ' + globalRate + " " + rateTimeline, {silent: true});
  result = result.stdout.toString().replace(/(\r\n|\n|\r)/gm, "");
  return result
}

async function pythonComputePerSecondRate(globalRate, rateTimeline) {
  return new Promise ((resolve, reject) => {
    const pythonProcess = spawn('python',["test/utils/rate_calculation/computePerSecondRate.py", globalRate, rateTimeline]);
    pythonProcess.stdout.on('data', (data) => {
      var adjustedRate = ((data.toString().split("E")[0]).replace("\n", ""));
      if (adjustedRate.includes(".")) {
        adjustedRate = adjustedRate.concat("0")
      }
      resolve(adjustedRate.replace(".", ""))
    });
  })
}

function assertBnEq (a, b, message) {
  assert(a.eq(b), `${message} (${a.valueOf()} != ${b.valueOf()})`)
}

module.exports = {
  bashComputePerSecondRate,
  pythonComputePerSecondRate,
  assertBnEq
}
