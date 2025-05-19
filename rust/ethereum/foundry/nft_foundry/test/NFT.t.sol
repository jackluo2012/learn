// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

import {Test, console} from "forge-std/Test.sol";
import {NFT, MintPriceNotPaid} from "../src/NFT.sol";

contract NFTTest is Test {
    NFT public nft;

    function setUp() public {
        // 创建合约实例
        nft = new NFT("NFT", "NFT", "baseUri");
    }

    function test_RevertMintWithoutValue() public {
        // 于预期和验证合约函数在特定条件下是否触发错误的测试工具
        vm.expectRevert(MintPriceNotPaid.selector);
        nft.mintTo(address(1));
    }
    function test_MintPricePaid () public {
        // 模拟一个用户试图支付铸币费用的场景
        nft.mintTo{value: 0.08 ether}(address(1));
    }
    function test_RevertMintToZeroAddress() public {
        vm.expectRevert("INVALID_RECIPIENT");
        nft.mintTo{value: 0.08 ether}(address(0));
	}
    
}
