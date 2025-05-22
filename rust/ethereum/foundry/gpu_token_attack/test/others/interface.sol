// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.10;

import "forge-std/Test.sol";
import "../interface.sol";

interface LSWUSDC {
    function maxFlashLoan(address token) external view returns(uint256);
    function flashFee(address token, uint256 amount) external view returns(uint256);
    function flashLoan(address receiver, address token, uint256 amount, bytes calldata data) external;
    function deposit(uint256 amount, address to) external returns(uint256);
    function redeem(uint256 shares, address receiver, address owner) external;
}