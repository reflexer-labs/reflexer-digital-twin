// Copyright (C) 2020 Maker Ecosystem Growth Holdings, INC, Reflexer Labs, INC.

// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

pragma solidity ^0.6.7;

import "./RateSetterMath.sol";

abstract contract OracleLike {
    function getResultWithValidity() virtual external returns (uint256, bool);
}
abstract contract OracleRelayerLike {
    function redemptionPrice() virtual external returns (uint256);
    function modifyParameters(bytes32,uint256) virtual external;
}
abstract contract StabilityFeeTreasuryLike {
    function getAllowance(address) virtual external view returns (uint, uint);
    function systemCoin() virtual external view returns (address);
    function pullFunds(address, address, uint) virtual external;
}
abstract contract PIDCalculator {
    function computeRate(uint256, uint256, uint256) virtual external returns (uint256);
    function rt(uint256, uint256, uint256) virtual external view returns (uint256);
    function pscl() virtual external view returns (uint256);
    function tlv() virtual external view returns (uint256);
}

contract RateSetter is RateSetterMath {
  // --- Auth ---
  mapping (address => uint) public authorizedAccounts;
  function addAuthorization(address account) external isAuthorized { authorizedAccounts[account] = 1; }
  function removeAuthorization(address account) external isAuthorized { authorizedAccounts[account] = 0; }
  modifier isAuthorized {
      require(authorizedAccounts[msg.sender] == 1, "RateSetter/account-not-authorized");
      _;
  }

  // Settlement flag
  uint256 public contractEnabled;                 // [0 or 1]
  // Last recorded system coin market price
  uint256 public latestMarketPrice;               // [ray]
  // When the price feed was last updated
  uint256 public lastUpdateTime;                  // [timestamp]
  // Enforced gap between calls
  uint256 public updateRateDelay;                 // [seconds]
  // Starting reward for the feeReceiver of a updateRate call
  uint256 public baseUpdateCallerReward;          // [wad]
  // Max possible reward for the feeReceiver of a updateRate call
  uint256 public maxUpdateCallerReward;           // [wad]
  // Rate applied to baseUpdateCallerReward every extra second passed beyond updateRateDelay seconds since the last updateRate call
  uint256 public perSecondCallerRewardIncrease;   // [ray]

  // --- System Dependencies ---
  // OSM or medianizer for the system coin
  OracleLike                public orcl;
  // OracleRelayer where the redemption price is stored
  OracleRelayerLike         public oracleRelayer;
  // SF treasury
  StabilityFeeTreasuryLike  public treasury;
  // Calculator for the redemption rate
  PIDCalculator             public pidCalculator;

  // --- Events ---
  event UpdateRedemptionRate(
      uint marketPrice,
      uint redemptionPrice,
      uint redemptionRate
  );
  event FailUpdateRedemptionRate(
      bytes reason
  );
  event FailRewardCaller(bytes revertReason, address feeReceiver, uint256 amount);
  event FailUpdateOracle(bytes revertReason, address orcl);

  constructor(
    address oracleRelayer_,
    address orcl_,
    address treasury_,
    address pidCalculator_,
    uint256 baseUpdateCallerReward_,
    uint256 maxUpdateCallerReward_,
    uint256 perSecondCallerRewardIncrease_,
    uint256 updateRateDelay_
  ) public {
      if (address(treasury_) != address(0)) {
        require(StabilityFeeTreasuryLike(treasury_).systemCoin() != address(0), "RateSetter/treasury-coin-not-set");
      }
      require(maxUpdateCallerReward_ >= baseUpdateCallerReward_, "RateSetter/invalid-max-caller-reward");
      require(perSecondCallerRewardIncrease_ >= RAY, "RateSetter/invalid-per-second-reward-increase");
      authorizedAccounts[msg.sender]  = 1;
      oracleRelayer                   = OracleRelayerLike(oracleRelayer_);
      orcl                            = OracleLike(orcl_);
      treasury                        = StabilityFeeTreasuryLike(treasury_);
      pidCalculator                    = PIDCalculator(pidCalculator_);
      baseUpdateCallerReward          = baseUpdateCallerReward_;
      maxUpdateCallerReward           = maxUpdateCallerReward_;
      perSecondCallerRewardIncrease   = perSecondCallerRewardIncrease_;
      updateRateDelay                 = updateRateDelay_;
      contractEnabled                 = 1;
  }

  // --- Boolean Logic ---
  function either(bool x, bool y) internal pure returns (bool z) {
      assembly{ z := or(x, y)}
  }

  // --- Management ---
  function modifyParameters(bytes32 parameter, address addr) external isAuthorized {
      require(contractEnabled == 1, "RateSetter/contract-not-enabled");
      if (parameter == "orcl") orcl = OracleLike(addr);
      else if (parameter == "oracleRelayer") oracleRelayer = OracleRelayerLike(addr);
      else if (parameter == "treasury") {
        require(StabilityFeeTreasuryLike(addr).systemCoin() != address(0), "RateSetter/treasury-coin-not-set");
        treasury = StabilityFeeTreasuryLike(addr);
      }
      else if (parameter == "pidCalculator") {
        pidCalculator = PIDCalculator(addr);
      }
      else revert("RateSetter/modify-unrecognized-param");
  }
  function modifyParameters(bytes32 parameter, uint256 val) external isAuthorized {
      require(contractEnabled == 1, "RateSetter/contract-not-enabled");
      if (parameter == "baseUpdateCallerReward") {
        require(val <= maxUpdateCallerReward, "RateSetter/invalid-base-caller-reward");
        baseUpdateCallerReward = val;
      }
      else if (parameter == "maxUpdateCallerReward") {
        require(val >= baseUpdateCallerReward, "RateSetter/invalid-max-caller-reward");
        maxUpdateCallerReward = val;
      }
      else if (parameter == "perSecondCallerRewardIncrease") {
        require(val >= RAY, "RateSetter/invalid-caller-reward-increase");
        perSecondCallerRewardIncrease = val;
      }
      else if (parameter == "updateRateDelay") {
        require(val >= 0, "RateSetter/invalid-call-gap-length");
        updateRateDelay = val;
      }
      else revert("RateSetter/modify-unrecognized-param");
  }
  function disableContract() external isAuthorized {
      contractEnabled = 0;
  }

  // --- Treasury ---
  function treasuryAllowance() public view returns (uint256) {
      (uint total, uint perBlock) = treasury.getAllowance(address(this));
      return minimum(total, perBlock);
  }
  function getCallerReward() public view returns (uint256) {
      uint256 timeElapsed = (lastUpdateTime == 0) ? updateRateDelay : subtract(now, lastUpdateTime);
      if (timeElapsed < updateRateDelay) {
          return 0;
      }
      uint256 baseReward = baseUpdateCallerReward;
      if (subtract(timeElapsed, updateRateDelay) > 0) {
          baseReward = rmultiply(rpower(perSecondCallerRewardIncrease, subtract(timeElapsed, updateRateDelay), RAY), baseReward);
      }
      uint256 maxReward = minimum(maxUpdateCallerReward, treasuryAllowance() / RAY);
      if (baseReward > maxReward) {
          baseReward = maxReward;
      }
      return baseReward;
  }
  function rewardCaller(address proposedFeeReceiver, uint256 reward) internal {
      if (address(treasury) == proposedFeeReceiver) return;
      if (address(treasury) == address(0) || reward == 0) return;
      address finalFeeReceiver = (proposedFeeReceiver == address(0)) ? msg.sender : proposedFeeReceiver;
      try treasury.pullFunds(finalFeeReceiver, treasury.systemCoin(), reward) {}
      catch(bytes memory revertReason) {
          emit FailRewardCaller(revertReason, finalFeeReceiver, reward);
      }
  }

  // --- Feedback Mechanism ---
  function updateRate(address feeReceiver) public {
      require(contractEnabled == 1, "RateSetter/contract-not-enabled");
      // Check delay between calls
      require(either(subtract(now, lastUpdateTime) >= updateRateDelay, lastUpdateTime == 0), "RateSetter/wait-more");
      // Get price feed updates
      (uint256 marketPrice, bool hasValidValue) = orcl.getResultWithValidity();
      // If the oracle has a value
      require(hasValidValue, "RateSetter/invalid-oracle-value");
      // If the price is non-zero
      require(marketPrice > 0, "RateSetter/null-price");
      // Get the latest redemption price
      uint redemptionPrice = oracleRelayer.redemptionPrice();
      // Get the caller's reward
      uint256 callerReward = getCallerReward();
      // Store the latest market price
      latestMarketPrice = ray(marketPrice);
      // Validate the seed
      uint256 tlv       = pidCalculator.tlv();
      uint256 iapcr     = rpower(pidCalculator.pscl(), tlv, RAY);
      uint256 validated = pidCalculator.computeRate(
          marketPrice,
          redemptionPrice,
          iapcr
      );
      // Store the timestamp of the update
      lastUpdateTime = now;
      // Update the rate inside the system (if it doesn't throw)
      try oracleRelayer.modifyParameters("redemptionRate", validated) {
        // Emit success event
        emit UpdateRedemptionRate(
          ray(marketPrice),
          redemptionPrice,
          validated
        );
      }
      catch(bytes memory revertReason) {
        emit FailUpdateRedemptionRate(
          revertReason
        );
      }
      // Pay the caller for updating the rate
      rewardCaller(feeReceiver, callerReward);
  }

  // --- Getters ---
  function getRedemptionAndMarketPrices() public returns (uint256 marketPrice, uint256 redemptionPrice) {
      (marketPrice, ) = orcl.getResultWithValidity();
      redemptionPrice = oracleRelayer.redemptionPrice();
  }
}
