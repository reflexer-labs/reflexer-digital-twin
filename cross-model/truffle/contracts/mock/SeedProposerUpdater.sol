pragma solidity 0.6.7;

abstract contract Setter {
    function modifyParameters(bytes32, address) virtual public;
}

contract SeedProposerUpdater {
    bytes32 ag = bytes32("seedProposer");

    function modifyParameters(address who, address val) public {
      Setter(who).modifyParameters(ag, val);
    }
}
