pragma solidity 0.6.7;

import "../setter/RateSetterMath.sol";

abstract contract OracleLike {
    function getResultWithValidity() virtual external returns (uint256, bool);
    function lastUpdateTime() virtual external view returns (uint64);
}
abstract contract OracleRelayerLike {
    function redemptionPrice() virtual external returns (uint256);
    function modifyParameters(bytes32,uint256) virtual external;
}
abstract contract PIDValidator {
    function validateSeed(uint256, uint256, uint256, uint256, uint256, uint256) virtual external returns (uint256);
    function rt(uint256, uint256, uint256) virtual external view returns (uint256);
    function pscl() virtual external view returns (uint256);
    function tlv() virtual external view returns (uint256);
    function lprad() virtual external view returns (uint256);
    function uprad() virtual external view returns (uint256);
    function adi() virtual external view returns (uint256);
    function adat() external virtual view returns (uint256);
}

contract MockRateSetter is RateSetterMath {
    // --- System Dependencies ---
    // OSM or medianizer for the system coin
    OracleLike                public orcl;
    // OracleRelayer where the redemption price is stored
    OracleRelayerLike         public oracleRelayer;
    // Calculator for the redemption rate
    PIDValidator              public pidValidator;

    constructor(address orcl_, address oracleRelayer_, address pidValidator_) public {
        oracleRelayer  = OracleRelayerLike(oracleRelayer_);
        orcl           = OracleLike(orcl_);
        pidValidator   = PIDValidator(pidValidator_);
    }

    function modifyParameters(bytes32 parameter, address addr) external {
        if (parameter == "orcl") orcl = OracleLike(addr);
        else if (parameter == "oracleRelayer") oracleRelayer = OracleRelayerLike(addr);
        else if (parameter == "pidValidator") {
          pidValidator = PIDValidator(addr);
        }
        else revert("RateSetter/modify-unrecognized-param");
    }

    function updateRate(uint seed, address feeReceiver) public {
        // Get price feed updates
        (uint256 marketPrice, bool hasValidValue) = orcl.getResultWithValidity();
        // If the oracle has a value
        require(hasValidValue, "MockRateSetter/invalid-oracle-value");
        // Get the latest redemption price
        uint redemptionPrice = oracleRelayer.redemptionPrice();
        // Validate the seed
        uint256 tlv       = pidValidator.tlv();
        uint256 iapcr     = rpower(pidValidator.pscl(), tlv, RAY);
        uint256 uad       = rmultiply(pidValidator.lprad(), rpower(pidValidator.adi(), pidValidator.adat(), RAY));
        uad               = (uad == 0) ? pidValidator.uprad() : uad;
        uint256 validated = pidValidator.validateSeed(
            seed,
            rpower(seed, pidValidator.rt(marketPrice, redemptionPrice, iapcr), RAY),
            marketPrice,
            redemptionPrice,
            iapcr,
            uad
        );
        // Update the rate inside the system (if it doesn't throw)
        try oracleRelayer.modifyParameters("redemptionRate", validated) {}
        catch(bytes memory revertReason) {}
    }

    function iapcr() public view returns (uint256) {
        return rpower(pidValidator.pscl(), pidValidator.tlv(), RAY);
    }
    function adjustedAllowedDeviation() public view returns (uint256) {
        uint256 uad = rmultiply(pidValidator.lprad(), rpower(pidValidator.adi(), pidValidator.adat(), RAY));
        uad         = (uad == 0) ? pidValidator.uprad() : uad;
        return uad;
    }
    function getRTAdjustedSeed(uint seed, uint marketPrice, uint redemptionPrice) public returns (uint256) {
        return rpower(seed, rpower(seed, pidValidator.rt(marketPrice, redemptionPrice, iapcr()), RAY), RAY);
    }
}
