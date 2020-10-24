/// PScaledGlobalValidator.sol

pragma solidity ^0.6.7;

import "../../math/SafeMath.sol";
import "../../math/SignedSafeMath.sol";

contract PScaledGlobalValidator is SafeMath, SignedSafeMath {
    // --- Authorities ---
    mapping (address => uint) public authorities;
    function addAuthority(address account) external isAuthority { authorities[account] = 1; }
    function removeAuthority(address account) external isAuthority { authorities[account] = 0; }
    modifier isAuthority {
        require(authorities[msg.sender] == 1, "PScaledGlobalValidator/not-an-authority");
        _;
    }

    // --- Readers ---
    mapping (address => uint) public readers;
    function addReader(address account) external isAuthority { readers[account] = 1; }
    function removeReader(address account) external isAuthority { readers[account] = 0; }
    modifier isReader {
        require(readers[msg.sender] == 1, "PScaledGlobalValidator/not-a-reader");
        _;
    }

    // --- Structs ---
    struct DeviationObservation {
        uint timestamp;
        int  proportional;
    }

    // -- Static & Default Variables ---
    int256 internal Kp;                              // [EIGHTEEN_DECIMAL_NUMBER]
    uint256 internal noiseBarrier;                   // [EIGHTEEN_DECIMAL_NUMBER]
    uint256 internal defaultRedemptionRate;          // [TWENTY_SEVEN_DECIMAL_NUMBER]
    uint256 internal feedbackOutputUpperBound;       // [TWENTY_SEVEN_DECIMAL_NUMBER]
    int256  internal feedbackOutputLowerBound;       // [TWENTY_SEVEN_DECIMAL_NUMBER]
    uint256 internal periodSize;                     // [seconds]

    // --- Fluctuating/Dynamic Variables ---
    DeviationObservation[] internal deviationObservations;
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
        uint256 periodSize_,
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
        require(lowerPrecomputedRateAllowedDeviation_ < EIGHTEEN_DECIMAL_NUMBER, "PScaledGlobalValidator/invalid-lprad");
        require(upperPrecomputedRateAllowedDeviation_ <= lowerPrecomputedRateAllowedDeviation_, "PScaledGlobalValidator/invalid-uprad");
        require(allowedDeviationIncrease_ <= TWENTY_SEVEN_DECIMAL_NUMBER, "PScaledGlobalValidator/invalid-adi");
        require(Kp_ != 0, "PScaledGlobalValidator/null-sg");
        require(
          feedbackOutputUpperBound_ <= multiply(TWENTY_SEVEN_DECIMAL_NUMBER, EIGHTEEN_DECIMAL_NUMBER) &&
          feedbackOutputLowerBound_ >= -int(multiply(TWENTY_SEVEN_DECIMAL_NUMBER, EIGHTEEN_DECIMAL_NUMBER)) && feedbackOutputLowerBound_ < 0,
          "PScaledGlobalValidator/invalid-foub-or-folb"
        );
        require(periodSize_ > 0, "PScaledGlobalValidator/invalid-ps");
        require(uint(importedState[0]) <= now, "PScaledGlobalValidator/invalid-imported-time");
        require(noiseBarrier_ <= EIGHTEEN_DECIMAL_NUMBER, "PScaledGlobalValidator/invalid-nb");
        authorities[msg.sender]              = 1;
        readers[msg.sender]                  = 1;
        feedbackOutputUpperBound             = feedbackOutputUpperBound_;
        feedbackOutputLowerBound             = feedbackOutputLowerBound_;
        periodSize                           = periodSize_;
        Kp                                   = Kp_;
        lowerPrecomputedRateAllowedDeviation = lowerPrecomputedRateAllowedDeviation_;
        upperPrecomputedRateAllowedDeviation = upperPrecomputedRateAllowedDeviation_;
        allowedDeviationIncrease             = allowedDeviationIncrease_;
        minRateTimeline                      = minRateTimeline_;
        noiseBarrier                         = noiseBarrier_;
        lastUpdateTime                       = uint(importedState[0]);
        if (importedState[1] > 0 && importedState[2] > 0) {
          deviationObservations.push(
            DeviationObservation(uint(importedState[1]), importedState[2])
          );
        }
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
        else revert("PScaledGlobalValidator/modify-unrecognized-param");
    }
    function modifyParameters(bytes32 parameter, uint256 val) external isAuthority {
        if (parameter == "nb") {
          require(val <= EIGHTEEN_DECIMAL_NUMBER, "PScaledGlobalValidator/invalid-nb");
          noiseBarrier = val;
        }
        else if (parameter == "ps") {
          require(val > 0, "PScaledGlobalValidator/null-ps");
          periodSize = val;
        }
        else if (parameter == "mrt") {
          require(both(val > 0, val <= defaultGlobalTimeline), "PScaledGlobalValidator/invalid-mrt");
          minRateTimeline = val;
        }
        else if (parameter == "foub") {
          require(val <= multiply(TWENTY_SEVEN_DECIMAL_NUMBER, EIGHTEEN_DECIMAL_NUMBER), "PScaledGlobalValidator/big-foub");
          feedbackOutputUpperBound = val;
        }
        else if (parameter == "lprad") {
          require(val <= EIGHTEEN_DECIMAL_NUMBER && val >= upperPrecomputedRateAllowedDeviation, "PScaledGlobalValidator/invalid-lprad");
          lowerPrecomputedRateAllowedDeviation = val;
        }
        else if (parameter == "uprad") {
          require(val <= EIGHTEEN_DECIMAL_NUMBER && val <= lowerPrecomputedRateAllowedDeviation, "PScaledGlobalValidator/invalid-uprad");
          upperPrecomputedRateAllowedDeviation = val;
        }
        else if (parameter == "adi") {
          require(val <= TWENTY_SEVEN_DECIMAL_NUMBER, "PScaledGlobalValidator/invalid-adi");
          allowedDeviationIncrease = val;
        }
        else if (parameter == "dgt") {
          require(val > 0, "PScaledGlobalValidator/invalid-dgt");
          defaultGlobalTimeline = val;
        }
        else revert("PScaledGlobalValidator/modify-unrecognized-param");
    }
    function modifyParameters(bytes32 parameter, int256 val) external isAuthority {
        if (parameter == "folb") {
          require(
            val >= -int(multiply(TWENTY_SEVEN_DECIMAL_NUMBER, EIGHTEEN_DECIMAL_NUMBER)) && val < 0,
            "PScaledGlobalValidator/invalid-folb"
          );
          feedbackOutputLowerBound = val;
        }
        else if (parameter == "sg") {
          require(val != 0, "PScaledGlobalValidator/null-sg");
          Kp = val;
        }
        else revert("PScaledGlobalValidator/modify-unrecognized-param");
    }

    // --- P Specific Math ---
    function riemannSum(int x, int y) internal pure returns (int z) {
        return addition(x, y) / 2;
    }
    function absolute(int x) internal pure returns (uint z) {
        z = (x < 0) ? uint(-x) : uint(x);
    }

    // --- PI Utils ---
    function oll() public isReader view returns (uint256) {
        return deviationObservations.length;
    }
    function getBoundedRedemptionRate(int pOutput) public isReader view returns (uint256, uint256) {
        int  boundedPOutput = pOutput;
        uint newRedemptionRate;
        uint rateTimeline = defaultGlobalTimeline;

        if (pOutput < feedbackOutputLowerBound) {
          boundedPOutput = feedbackOutputLowerBound;
        } else if (pOutput > int(feedbackOutputUpperBound)) {
          boundedPOutput = int(feedbackOutputUpperBound);
        }

        bool negativeOutputExceedsHundred = (boundedPOutput < 0 && -boundedPOutput >= int(defaultRedemptionRate));
        if (negativeOutputExceedsHundred) {
          rateTimeline = divide(multiply(rateTimeline, TWENTY_SEVEN_DECIMAL_NUMBER), uint(-int(boundedPOutput)));
          if (rateTimeline == 0) {
            rateTimeline = (minRateTimeline == 0) ? 1 : minRateTimeline;
          }
          newRedemptionRate   = uint(addition(int(defaultRedemptionRate), -int(NEGATIVE_RATE_LIMIT)));
        } else {
          if (boundedPOutput < 0 && boundedPOutput <= -int(NEGATIVE_RATE_LIMIT)) {
            newRedemptionRate = uint(addition(int(defaultRedemptionRate), -int(NEGATIVE_RATE_LIMIT)));
          } else {
            newRedemptionRate = uint(addition(int(defaultRedemptionRate), boundedPOutput));
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
    function getGainAdjustedPOutput(int proportionalTerm) public isReader view returns (int256) {
        return multiply(proportionalTerm, int(Kp)) / int(EIGHTEEN_DECIMAL_NUMBER);
    }

    // --- Rate Validation ---
    function validateSeed(
      uint seed,
      uint inputAccumulatedPreComputedRate,
      uint marketPrice,
      uint redemptionPrice,
      uint ,
      uint precomputedAllowedDeviation
    ) external returns (uint256) {
        require(seedProposer == msg.sender, "PScaledGlobalValidator/invalid-msg-sender");
        require(subtract(now, lastUpdateTime) >= periodSize || lastUpdateTime == 0, "PScaledGlobalValidator/wait-more");
        uint256 scaledMarketPrice = multiply(marketPrice, 10**9);
        int256 proportionalTerm = multiply(subtract(int(redemptionPrice), int(scaledMarketPrice)), int(TWENTY_SEVEN_DECIMAL_NUMBER)) / int(redemptionPrice);
        deviationObservations.push(DeviationObservation(now, proportionalTerm));
        lastUpdateTime = now;
        int pOutput = getGainAdjustedPOutput(proportionalTerm);
        if (
          breaksNoiseBarrier(absolute(pOutput), redemptionPrice) &&
          pOutput != 0
        ) {
          (uint newRedemptionRate, ) = getBoundedRedemptionRate(pOutput);
          uint256 sanitizedAllowedDeviation =
            (precomputedAllowedDeviation > upperPrecomputedRateAllowedDeviation) ?
            upperPrecomputedRateAllowedDeviation : precomputedAllowedDeviation;
          require(
            correctPreComputedRate(inputAccumulatedPreComputedRate, newRedemptionRate, sanitizedAllowedDeviation),
            "PScaledGlobalValidator/invalid-seed"
          );
          return seed;
        } else {
          return TWENTY_SEVEN_DECIMAL_NUMBER;
        }
    }
    function getNextRedemptionRate(uint marketPrice, uint redemptionPrice)
      public isReader view returns (uint256, int256, uint256) {
        uint256 scaledMarketPrice = multiply(marketPrice, 10**9);
        int256 proportionalTerm   = multiply(subtract(int(redemptionPrice), int(scaledMarketPrice)), int(TWENTY_SEVEN_DECIMAL_NUMBER)) / int(redemptionPrice);
        int pOutput               = getGainAdjustedPOutput(proportionalTerm);
        if (
          breaksNoiseBarrier(absolute(pOutput), redemptionPrice) &&
          pOutput != 0
        ) {
          (uint newRedemptionRate, uint rateTimeline) = getBoundedRedemptionRate(pOutput);
          return (newRedemptionRate, proportionalTerm, rateTimeline);
        } else {
          return (TWENTY_SEVEN_DECIMAL_NUMBER, proportionalTerm, defaultGlobalTimeline);
        }
    }

    // --- Parameter Getters ---
    function rt(uint marketPrice, uint redemptionPrice, uint IGNORED) external isReader view returns (uint256) {
        (, , uint rateTimeline) = getNextRedemptionRate(marketPrice, redemptionPrice);
        return rateTimeline;
    }
    function sg() external isReader view returns (int256) {
        return Kp;
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
    function pscl() external isReader view returns (int256) {
        return int(TWENTY_SEVEN_DECIMAL_NUMBER);
    }
    function ps() external isReader view returns (uint256) {
        return periodSize;
    }
    function dos(uint256 i) external isReader view returns (uint256, int256) {
        return (deviationObservations[i].timestamp, deviationObservations[i].proportional);
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
        if (elapsed <= periodSize) {
          return 0;
        }
        return subtract(elapsed, periodSize);
    }
    function tlv() external isReader view returns (uint256) {
        uint elapsed = (lastUpdateTime == 0) ? 0 : subtract(now, lastUpdateTime);
        return elapsed;
    }
}
