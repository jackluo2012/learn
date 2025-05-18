// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import "forge-std/Test.sol";

contract ContractBTest is Test {
    uint256 testNumber;

    function setUp() public {
        testNumber = 42;
    }

    function testFail_Subtract43() public {
        vm.expectRevert(stdError.arithmeticError);
        console2.log("currentNumber= %d", testNumber);
        testNumber -= 43;
    }
}

