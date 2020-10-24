/// MockMockOracleRelayer.sol

pragma solidity ^0.6.7;

contract MockOracleRelayer {
    // The force that changes the system users' incentives by changing the redemption price
    uint256 public redemptionRate;
    // Last time when the redemption price was changed
    uint256 public redemptionPriceUpdateTime;
    // Virtual redemption price (not the most updated value)
    uint256 internal _redemptionPrice;

    constructor(uint initialRedemptionPrice) public {
        redemptionRate   = RAY;
        _redemptionPrice = initialRedemptionPrice;
    }

    // --- Math ---
    uint constant RAY = 10 ** 27;

    function subtract(uint x, uint y) internal pure returns (uint z) {
      z = x - y;
      require(z <= x);
    }
    function multiply(uint x, uint y) internal pure returns (uint z) {
      require(y == 0 || (z = x * y) / y == x);
    }
    function rmultiply(uint x, uint y) internal pure returns (uint z) {
      // alsites rounds down
      z = multiply(x, y) / RAY;
    }
    function rpower(uint x, uint n, uint base) internal pure returns (uint z) {
      assembly {
          switch x case 0 {switch n case 0 {z := base} default {z := 0}}
          default {
              switch mod(n, 2) case 0 { z := base } default { z := x }
              let half := div(base, 2)  // for rounding.
              for { n := div(n, 2) } n { n := div(n,2) } {
                  let xx := mul(x, x)
                  if iszero(eq(div(xx, x), x)) { revert(0,0) }
                  let xxRound := add(xx, half)
                  if lt(xxRound, xx) { revert(0,0) }
                  x := div(xxRound, base)
                  if mod(n,2) {
                      let zx := mul(z, x)
                      if and(iszero(iszero(x)), iszero(eq(div(zx, x), z))) { revert(0,0) }
                      let zxRound := add(zx, half)
                      if lt(zxRound, zx) { revert(0,0) }
                      z := div(zxRound, base)
                  }
              }
          }
      }
    }

    // --- Administration ---
    function modifyParameters(bytes32 parameter, uint data) external {
      if (parameter == "redemptionPrice") _redemptionPrice = data;
      else if (parameter == "redemptionRate") {
        require(now == redemptionPriceUpdateTime, "MockOracleRelayer/redemption-price-not-updated");
        redemptionRate = data;
      }
    }

    // --- Redemption Price Update ---
    /**
    * @notice Update the redemption price according to the current redemption rate
    */
    function updateRedemptionPrice() internal returns (uint) {
      // Update redemption price
      _redemptionPrice = rmultiply(
        rpower(redemptionRate, subtract(now, redemptionPriceUpdateTime), RAY),
        _redemptionPrice
      );
      if (_redemptionPrice == 0) _redemptionPrice = 1;
      redemptionPriceUpdateTime = now;
      // Return updated redemption price
      return _redemptionPrice;
    }
    /**
    * @notice Fetch the latest redemption price by first updating it
    */
    function redemptionPrice() public returns (uint) {
      if (now > redemptionPriceUpdateTime) return updateRedemptionPrice();
      return _redemptionPrice;
    }
}
