// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.20;
import {Test, console} from "forge-std/Test.sol";

interface IERC20 {
    function balanceOf(address) external view returns (uint256);
    function transfer(address, uint256) external returns (bool);
    function decimals() external view returns (uint8);
}

contract PEPETransferTest is Test {
    IERC20 pepe;
    address myAddress = 0xF977814e90dA44bFA03b6295A0616a897441aceC;
    address recipient = 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045;
    address pepeAddress = 0x6982508145454Ce325dDbE47a25d4ec3d2311933;

    function setUp() public {
        pepe = IERC20(pepeAddress);
        vm.startPrank(myAddress);
    }

    function testPEPETransfer() public {
        uint256 recipientBalanceBefore = pepe.balanceOf(recipient);
        console.log("PEPE balance of recipient before: ", recipientBalanceBefore);
        pepe.transfer(recipient, 10000000);

        uint256 recipientBalanceAfter = pepe.balanceOf(recipient);
        // 记录转账后余额日志
        console.log("PEPE balance of recipient after: ", recipientBalanceAfter); 
    }
}