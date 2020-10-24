/// PIRawGlobalValidator.sol

pragma solidity ^0.6.7;

import "../../math/SafeMath.sol";
import "../../math/SignedSafeMath.sol";

contract PIRawGlobalValidator is SafeMath, SignedSafeMath {
    // --- Authorities ---
    mapping (address => uint) public authorities;
    function addAuthority(address account) external isAuthority { authorities[account] = 1; }
    function removeAuthority(address account) external isAuthority { authorities[account] = 0; }
    modifier isAuthority {
        require(authorities[msg.sender] == 1, "PIRawGlobalValidator/not-an-authority");
        _;
    }

    // --- Readers ---
    mapping (address => uint) public readers;
    function addReader(address account) external isAuthority { readers[account] = 1; }
    function removeReader(address account) external isAuthority { readers[account] = 0; }
    modifier isReader {
        require(readers[msg.sender] == 1, "PIRawGlobalValidator/not-a-reader");
        _;
    }

    // --- Structs ---
    struct ControllerGains {
        int Kp;                                      // [EIGHTEEN_DECIMAL_NUMBER]
        int Ki;                                      // [EIGHTEEN_DECIMAL_NUMBER]
    }
    struct DeviationObservation {
        uint timestamp;
        int  proportional;
        int  integral;
    }

    // -- Static & Default Variables ---
    ControllerGains internal controllerGains;
    uint256 internal noiseBarrier;                   // [EIGHTEEN_DECIMAL_NUMBER]
    uint256 internal defaultRedemptionRate;          // [TWENTY_SEVEN_DECIMAL_NUMBER]
    uint256 internal feedbackOutputUpperBound;       // [TWENTY_SEVEN_DECIMAL_NUMBER]
    int256  internal feedbackOutputLowerBound;       // [TWENTY_SEVEN_DECIMAL_NUMBER]
    uint256 internal integralPeriodSize;             // [seconds]

    // --- Fluctuating/Dynamic Variables ---
    DeviationObservation[] internal deviationObservations;
    int256[]               internal historicalCumulativeDeviations;

    int256  internal priceDeviationCumulative;             // [TWENTY_SEVEN_DECIMAL_NUMBER]
    uint256 internal perSecondCumulativeLeak;              // [TWENTY_SEVEN_DECIMAL_NUMBER]
    uint256 internal lowerPrecomputedRateAllowedDeviation; // [EIGHTEEN_DECIMAL_NUMBER]
    uint256 internal upperPrecomputedRateAllowedDeviation; // [EIGHTEEN_DECIMAL_NUMBER]
    uint256 internal allowedDeviationIncrease;             // [TWENTY_SEVEN_DECIMAL_NUMBER]
    uint256 internal minRateTimeline;                      // [seconds]
    uint256 internal lastUpdateTime;                       // [timestamp]
    uint256 internal defaultGlobalTimeline = 31536000;

    address public seedProposer;

    uint256 internal constant NEGATIVE_RATE_LIMIT         = TWENTY_SEVEN_DECIMAL_NUMBER - 1;
    uint256 internal constant TWENTY_SEVEN_DECIMAL_NUMBER = 10 ** 27;
    uint256 internal constant EIGHTEEN_DECIMAL_NUMBER     = 10 ** 18;

    constructor(
        int256 Kp_,
        int256 Ki_,
        uint256 perSecondCumulativeLeak_,
        uint256 integralPeriodSize_,
        uint256 lowerPrecomputedRateAllowedDeviation_,
        uint256 upperPrecomputedRateAllowedDeviation_,
        uint256 allowedDeviationIncrease_,
        uint256 noiseBarrier_,
        uint256 feedbackOutputUpperBound_,
        uint256 minRateTimeline_,
        int256  feedbackOutputLowerBound_,
        int256[] memory importedState
    ) public {
        defaultRedemptionRate                = TWENTY_SEVEN_DECIMAL_NUMBER;
        require(lowerPrecomputedRateAllowedDeviation_ < EIGHTEEN_DECIMAL_NUMBER, "PIRawGlobalValidator/invalid-lprad");
        require(upperPrecomputedRateAllowedDeviation_ <= lowerPrecomputedRateAllowedDeviation_, "PIRawGlobalValidator/invalid-uprad");
        require(allowedDeviationIncrease_ <= TWENTY_SEVEN_DECIMAL_NUMBER, "PIRawGlobalValidator/invalid-adi");
        require(Kp_ != 0, "PIRawGlobalValidator/null-sg");
        require(feedbackOutputUpperBound_ < subtract(subtract(uint(-1), defaultRedemptionRate), 1) && feedbackOutputLowerBound_ < 0, "PIRawGlobalValidator/invalid-foub-or-folb");
        require(integralPeriodSize_ > 0, "PIRawGlobalValidator/invalid-ips");
        require(minRateTimeline_ <= defaultGlobalTimeline, "PIRawGlobalValidator/invalid-mrt");
        require(uint(importedState[0]) <= now, "PIRawGlobalValidator/invalid-imported-time");
        require(noiseBarrier_ <= EIGHTEEN_DECIMAL_NUMBER, "PIRawGlobalValidator/invalid-nb");
        authorities[msg.sender]              = 1;
        readers[msg.sender]                  = 1;
        feedbackOutputUpperBound             = feedbackOutputUpperBound_;
        feedbackOutputLowerBound             = feedbackOutputLowerBound_;
        integralPeriodSize                   = integralPeriodSize_;
        controllerGains                      = ControllerGains(Kp_, Ki_);
        lowerPrecomputedRateAllowedDeviation = lowerPrecomputedRateAllowedDeviation_;
        upperPrecomputedRateAllowedDeviation = upperPrecomputedRateAllowedDeviation_;
        allowedDeviationIncrease             = allowedDeviationIncrease_;
        perSecondCumulativeLeak              = perSecondCumulativeLeak_;
        minRateTimeline                      = minRateTimeline_;
        priceDeviationCumulative             = importedState[3];
        noiseBarrier                         = noiseBarrier_;
        lastUpdateTime                       = uint(importedState[0]);
        if (importedState[4] > 0) {
          deviationObservations.push(
            DeviationObservation(uint(importedState[4]), importedState[1], importedState[2])
          );
        }
        historicalCumulativeDeviations.push(priceDeviationCumulative);
    }

    // --- Boolean Logic ---
    function both(bool x, bool y) internal pure returns (bool z) {
        assembly{ z := and(x, y)}
    }

    // --- Administration ---
    function modifyParameters(bytes32 parameter, address addr) external isAuthority {
        if (parameter == "seedProposer") {
          readers[seedProposer] = 0;
          seedProposer = addr;
          readers[seedProposer] = 1;
        }
        else revert("PIRawGlobalValidator/modify-unrecognized-param");
    }
    function modifyParameters(bytes32 parameter, uint256 val) external isAuthority {
        if (parameter == "nb") {
          require(val <= EIGHTEEN_DECIMAL_NUMBER, "PIRawGlobalValidator/invalid-nb");
          noiseBarrier = val;
        }
        else if (parameter == "ips") {
          require(val > 0, "PIRawGlobalValidator/null-ips");
          integralPeriodSize = val;
        }
        else if (parameter == "mrt") {
          require(both(val > 0, val <= defaultGlobalTimeline), "PIRawGlobalValidator/invalid-mrt");
          minRateTimeline = val;
        }
        else if (parameter == "foub") {
          require(val < subtract(subtract(uint(-1), defaultRedemptionRate), 1), "PIRawGlobalValidator/big-foub");
          feedbackOutputUpperBound = val;
        }
        else if (parameter == "pscl") {
          require(val <= TWENTY_SEVEN_DECIMAL_NUMBER, "PIRawGlobalValidator/invalid-pscl");
          perSecondCumulativeLeak = val;
        }
        else if (parameter == "lprad") {
          require(val <= EIGHTEEN_DECIMAL_NUMBER && val >= upperPrecomputedRateAllowedDeviation, "PIRawGlobalValidator/invalid-lprad");
          lowerPrecomputedRateAllowedDeviation = val;
        }
        else if (parameter == "uprad") {
          require(val <= EIGHTEEN_DECIMAL_NUMBER && val <= lowerPrecomputedRateAllowedDeviation, "PIRawGlobalValidator/invalid-uprad");
          upperPrecomputedRateAllowedDeviation = val;
        }
        else if (parameter == "adi") {
          require(val <= TWENTY_SEVEN_DECIMAL_NUMBER, "PIRawGlobalValidator/invalid-adi");
          allowedDeviationIncrease = val;
        }
        else if (parameter == "dgt") {
          require(val > 0, "PIRawGlobalValidator/invalid-dgt");
          defaultGlobalTimeline = val;
        }
        else revert("PIRawGlobalValidator/modify-unrecognized-param");
    }
    function modifyParameters(bytes32 parameter, int256 val) external isAuthority {
        if (parameter == "folb") {
          require(val < 0, "PIRawGlobalValidator/invalid-folb");
          feedbackOutputLowerBound = val;
        }
        else if (parameter == "sg") {
          require(val != 0, "PIRawGlobalValidator/null-sg");
          controllerGains.Kp = val;
        }
        else if (parameter == "ag") {
          controllerGains.Ki = val;
        }
        else if (parameter == "pdc") {
          require(controllerGains.Ki == 0, "PIRawGlobalValidator/cannot-set-pdc");
          priceDeviationCumulative = val;
        }
        else revert("PIRawGlobalValidator/modify-unrecognized-param");
    }

    // --- PI Specific Math ---
    function riemannSum(int x, int y) internal pure returns (int z) {
        return addition(x, y) / 2;
    }
    function absolute(int x) internal pure returns (uint z) {
        z = (x < 0) ? uint(-x) : uint(x);
    }

    // --- PI Utils ---
    function getLastProportionalTerm() public isReader view returns (int256) {
        if (oll() == 0) return 0;
        return deviationObservations[oll() - 1].proportional;
    }
    function getLastIntegralTerm() public isReader view returns (int256) {
        if (oll() == 0) return 0;
        return deviationObservations[oll() - 1].integral;
    }
    function oll() public isReader view returns (uint256) {
        return deviationObservations.length;
    }
    function getBoundedRedemptionRate(int piOutput) public isReader view returns (uint256, uint256) {
        int  boundedPIOutput = piOutput;
        uint newRedemptionRate;
        uint rateTimeline = defaultGlobalTimeline;

        if (piOutput < feedbackOutputLowerBound) {
          boundedPIOutput = feedbackOutputLowerBound;
        } else if (piOutput > int(feedbackOutputUpperBound)) {
          boundedPIOutput = int(feedbackOutputUpperBound);
        }

        bool negativeOutputExceedsHundred = (boundedPIOutput < 0 && -boundedPIOutput >= int(defaultRedemptionRate));
        if (negativeOutputExceedsHundred) {
          rateTimeline = divide(multiply(rateTimeline, TWENTY_SEVEN_DECIMAL_NUMBER), uint(-int(boundedPIOutput)));
          if (rateTimeline == 0) {
            rateTimeline = (minRateTimeline == 0) ? 1 : minRateTimeline;
          }
          newRedemptionRate   = uint(addition(int(defaultRedemptionRate), -int(NEGATIVE_RATE_LIMIT)));
        } else {
          if (boundedPIOutput < 0 && boundedPIOutput <= -int(NEGATIVE_RATE_LIMIT)) {
            newRedemptionRate = uint(addition(int(defaultRedemptionRate), -int(NEGATIVE_RATE_LIMIT)));
          } else {
            newRedemptionRate = uint(addition(int(defaultRedemptionRate), boundedPIOutput));
          }
        }

        return (newRedemptionRate, rateTimeline);
    }
    function breaksNoiseBarrier(uint piSum, uint redemptionPrice) public isReader view returns (bool) {
        uint deltaNoise = subtract(multiply(uint(2), EIGHTEEN_DECIMAL_NUMBER), noiseBarrier);
        return piSum >= subtract(divide(multiply(redemptionPrice, deltaNoise), EIGHTEEN_DECIMAL_NUMBER), redemptionPrice);
    }
    function correctPreComputedRate(uint precomputedRate, uint contractComputedRate, uint precomputedAllowedDeviation) public isReader view returns (bool) {
        if (precomputedRate == contractComputedRate) return true;
        bool withinBounds = (
          precomputedRate >= divide(multiply(contractComputedRate, precomputedAllowedDeviation), EIGHTEEN_DECIMAL_NUMBER) &&
          precomputedRate <= divide(multiply(contractComputedRate, subtract(multiply(uint(2), EIGHTEEN_DECIMAL_NUMBER), precomputedAllowedDeviation)), EIGHTEEN_DECIMAL_NUMBER)
        );
        bool sameSign = true;
        if (
          contractComputedRate < TWENTY_SEVEN_DECIMAL_NUMBER && precomputedRate >= TWENTY_SEVEN_DECIMAL_NUMBER ||
          contractComputedRate > TWENTY_SEVEN_DECIMAL_NUMBER && precomputedRate <= TWENTY_SEVEN_DECIMAL_NUMBER
        ) {
          sameSign = false;
        }
        return (withinBounds && sameSign);
    }
    function getNextPriceDeviationCumulative(int proportionalTerm, uint accumulatedLeak) public isReader view returns (int256, int256) {
        int256 lastProportionalTerm      = getLastProportionalTerm();
        uint256 timeElapsed              = (lastUpdateTime == 0) ? 0 : subtract(now, lastUpdateTime);
        int256 newTimeAdjustedDeviation  = multiply(riemannSum(proportionalTerm, lastProportionalTerm), int(timeElapsed));
        int256 leakedPriceCumulative     = divide(multiply(int(accumulatedLeak), priceDeviationCumulative), int(TWENTY_SEVEN_DECIMAL_NUMBER));

        return (
          addition(leakedPriceCumulative, newTimeAdjustedDeviation),
          newTimeAdjustedDeviation
        );
    }
    function getGainAdjustedPIOutput(int proportionalTerm, int integralTerm) public isReader view returns (int256) {
        (int adjustedProportional, int adjustedIntegral) = getGainAdjustedTerms(proportionalTerm, integralTerm);
        return addition(adjustedProportional, adjustedIntegral);
    }
    function getGainAdjustedTerms(int proportionalTerm, int integralTerm) public isReader view returns (int256, int256) {
        return (
          multiply(proportionalTerm, int(controllerGains.Kp)) / int(EIGHTEEN_DECIMAL_NUMBER),
          multiply(integralTerm, int(controllerGains.Ki)) / int(EIGHTEEN_DECIMAL_NUMBER)
        );
    }

    // --- Rate Validation/Calculation ---
    function validateSeed(
      uint seed,
      uint inputAccumulatedPreComputedRate,
      uint marketPrice,
      uint redemptionPrice,
      uint accumulatedLeak,
      uint precomputedAllowedDeviation
    ) external returns (uint256) {
        require(seedProposer == msg.sender, "PIRawGlobalValidator/invalid-msg-sender");
        require(precomputedAllowedDeviation <= EIGHTEEN_DECIMAL_NUMBER, "PIRawGlobalValidator/invalid-prad");
        require(subtract(now, lastUpdateTime) >= integralPeriodSize || lastUpdateTime == 0, "PIRawGlobalValidator/wait-more");
        int256 proportionalTerm = subtract(int(redemptionPrice), multiply(int(marketPrice), int(10**9)));
        updateDeviationHistory(proportionalTerm, accumulatedLeak);
        lastUpdateTime = now;
        int256 piOutput = getGainAdjustedPIOutput(proportionalTerm, priceDeviationCumulative);
        if (
          breaksNoiseBarrier(absolute(piOutput), redemptionPrice) &&
          piOutput != 0
        ) {
          (uint newRedemptionRate, ) = getBoundedRedemptionRate(piOutput);
          uint256 sanitizedAllowedDeviation =
            (precomputedAllowedDeviation > upperPrecomputedRateAllowedDeviation) ?
            upperPrecomputedRateAllowedDeviation : precomputedAllowedDeviation;
          require(
            correctPreComputedRate(inputAccumulatedPreComputedRate, newRedemptionRate, sanitizedAllowedDeviation),
            "PIRawGlobalValidator/invalid-seed"
          );
          return seed;
        } else {
          return TWENTY_SEVEN_DECIMAL_NUMBER;
        }
    }
    function updateDeviationHistory(int proportionalTerm, uint accumulatedLeak) internal {
        (int256 virtualDeviationCumulative, int256 nextTimeAdjustedDeviation) =
          getNextPriceDeviationCumulative(proportionalTerm, accumulatedLeak);
        priceDeviationCumulative = virtualDeviationCumulative;
        historicalCumulativeDeviations.push(priceDeviationCumulative);
        deviationObservations.push(DeviationObservation(now, proportionalTerm, priceDeviationCumulative));
    }
    function getNextRedemptionRate(uint marketPrice, uint redemptionPrice, uint accumulatedLeak)
      public isReader view returns (uint256, int256, int256, uint256) {
        int256 proportionalTerm = subtract(int(redemptionPrice), multiply(int(marketPrice), int(10**9)));
        (int cumulativeDeviation, ) = getNextPriceDeviationCumulative(proportionalTerm, accumulatedLeak);
        int piOutput = getGainAdjustedPIOutput(proportionalTerm, cumulativeDeviation);
        if (
          breaksNoiseBarrier(absolute(piOutput), redemptionPrice) &&
          piOutput != 0
        ) {
          (uint newRedemptionRate, uint rateTimeline) = getBoundedRedemptionRate(piOutput);
          return (newRedemptionRate, proportionalTerm, cumulativeDeviation, rateTimeline);
        } else {
          return (TWENTY_SEVEN_DECIMAL_NUMBER, proportionalTerm, cumulativeDeviation, defaultGlobalTimeline);
        }
    }

    // --- Parameter Getters ---
    function rt(uint marketPrice, uint redemptionPrice, uint accumulatedLeak) external isReader view returns (uint256) {
        (, , , uint rateTimeline) = getNextRedemptionRate(marketPrice, redemptionPrice, accumulatedLeak);
        return rateTimeline;
    }
    function sg() external isReader view returns (int256) {
        return controllerGains.Kp;
    }
    function ag() external isReader view returns (int256) {
        return controllerGains.Ki;
    }
    function nb() external isReader view returns (uint256) {
        return noiseBarrier;
    }
    function drr() external isReader view returns (uint256) {
        return defaultRedemptionRate;
    }
    function foub() external isReader view returns (uint256) {
        return feedbackOutputUpperBound;
    }
    function folb() external isReader view returns (int256) {
        return feedbackOutputLowerBound;
    }
    function ips() external isReader view returns (uint256) {
        return integralPeriodSize;
    }
    function dos(uint256 i) external isReader view returns (uint256, int256, int256) {
        return (deviationObservations[i].timestamp, deviationObservations[i].proportional, deviationObservations[i].integral);
    }
    function hcd(uint256 i) external isReader view returns (int256) {
        return historicalCumulativeDeviations[i];
    }
    function pdc() external isReader view returns (int256) {
        return priceDeviationCumulative;
    }
    function pscl() external isReader view returns (uint256) {
        return perSecondCumulativeLeak;
    }
    function lprad() external isReader view returns (uint256) {
        return lowerPrecomputedRateAllowedDeviation;
    }
    function uprad() external isReader view returns (uint256) {
        return upperPrecomputedRateAllowedDeviation;
    }
    function adi() external isReader view returns (uint256) {
        return allowedDeviationIncrease;
    }
    function mrt() external isReader view returns (uint256) {
        return minRateTimeline;
    }
    function lut() external isReader view returns (uint256) {
        return lastUpdateTime;
    }
    function dgt() external isReader view returns (uint256) {
        return defaultGlobalTimeline;
    }
    function adat() external isReader view returns (uint256) {
        uint elapsed = subtract(now, lastUpdateTime);
        if (elapsed < integralPeriodSize) {
          return 0;
        }
        return subtract(elapsed, integralPeriodSize);
    }
    function tlv() external isReader view returns (uint256) {
        uint elapsed = (lastUpdateTime == 0) ? 0 : subtract(now, lastUpdateTime);
        return elapsed;
    }
}
