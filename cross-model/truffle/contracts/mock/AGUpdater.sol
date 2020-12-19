pragma solidity 0.6.7;

abstract contract Setter {
    function modifyParameters(bytes32, uint) virtual public;
}

contract AGUpdater {
    bytes32 ag = bytes32("ag");

    function modifyParameters(address who, uint val) public {
      Setter(who).modifyParameters(ag, val);
    }
}
