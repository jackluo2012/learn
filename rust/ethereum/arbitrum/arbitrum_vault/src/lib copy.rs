// Only run this as a WASM if the export-abi feature is not set.
#![cfg_attr(not(any(feature = "export-abi", test)), no_main)]
extern crate alloc;

// Modules and imports
mod erc20;

use alloy_primitives::{Address, U256};
use stylus_sdk::{
    contract,
    call::{self, call, static_call, transfer_eth, Call, RawCall}, function_selector, msg, prelude::*
};
use crate::erc20::{Erc20, Erc20Params, Erc20Error};

/// Immutable definitions
struct StylusTokenParams;
impl Erc20Params for StylusTokenParams {
    const NAME: &'static str = "VAULT Token";
    const SYMBOL: &'static str = "VAULT";
    const DECIMALS: u8 = 18;
}

// Define the entrypoint as a Solidity storage object. The sol_storage! macro
// will generate Rust-equivalent structs with all fields mapped to Solidity-equivalent
// storage slots and types.
sol_storage! {
    #[entrypoint]
    struct StylusToken {
        // Allows erc20 to access StylusToken's storage and make calls
        #[borrow]
        Erc20<StylusTokenParams> erc20;
        uint totalSupply; 
        address asset;
    }
}

#[public]
#[inherit(Erc20<StylusTokenParams>)]
impl StylusToken {
     // 设置资产地址
     pub fn setAsset(&mut self, _asset: Address) -> Result<Address, Vec<u8>> {
        // 设置资产地址
        self.asset.set(_asset);
        Ok(_asset)
    }
    #[payable]
    // 存入资产到 Vault
    pub fn deposit(&mut self, amount: U256) -> Result<(), Vec<u8>> {
        // 检查资产地址
        let asset_addr = self.asset.get();
        if asset_addr == Address::ZERO {
            return Err(b"asset not set".to_vec());
        }
        if amount.is_zero() {
            return Err(b"amount is zero".to_vec());
        }

        // 组装 transferFrom 调用数据
        let selector = function_selector!("transferFrom(address,address,uint256)");
        let data = [
            &selector[..],
            &msg::sender().into_array(),      // from: 用户
            &contract::address().into_array(),// to: vault 合约
            &amount.to_be_bytes::<32>(),
        ].concat();

        // 调用资产合约的 transferFrom
        let call_result = call(Call::new(), asset_addr, &data);
        if call_result.is_err() {
            return Err(b"transferFrom failed".to_vec());
        }

        // shares 计算
        let supply = self.totalSupply.get();
        let shares = if supply == U256::ZERO {
            amount
        } else {
            amount.checked_mul(supply).ok_or(b"Overflow".to_vec())?
                .checked_div(self.totalAssets()?).ok_or(b"Divide by zero".to_vec())?
        };
        self.erc20.mint(msg::sender(), shares);
        Ok(())
    }

    pub fn withdraw(&mut self, amount: U256) -> Result<(), Vec<u8>> {
        let asset_addr = self.asset.get();
        if asset_addr == Address::ZERO {
            return Err(b"asset not set".to_vec());
        }
        let supply = self.totalSupply.get();
        let shares = if supply == U256::ZERO {
            amount
        } else {
            amount.checked_mul(supply).ok_or(b"Overflow".to_vec())?
                .checked_div(self.totalAssets()?).ok_or(b"Divide by zero".to_vec())?
        };

        self.erc20.burn(msg::sender(), shares)?;

        // 组装 transfer 调用数据
        let selector = function_selector!("transfer(address,uint256)");
        let data = [
            &selector[..],
            &msg::sender().into_array(),
            &amount.to_be_bytes::<32>(),
        ].concat();

        let call_result = call(Call::new(), asset_addr, &data);
        if call_result.is_err() {
            return Err(b"transfer failed".to_vec());
        }
        Ok(())
    }
    /// Mints tokens
    pub fn mint(&mut self, value: U256) -> Result<(), Erc20Error> {
        self.erc20.mint(msg::sender(), value)?;
        Ok(())
    }

    /// Mints tokens to another address
    pub fn mint_to(&mut self, to: Address, value: U256) -> Result<(), Erc20Error> {
        self.erc20.mint(to, value)?;
        Ok(())
    }

    /// Burns tokens
    pub fn burn(&mut self, value: U256) -> Result<(), Erc20Error> {
        self.erc20.burn(msg::sender(), value)?;
        Ok(())
    }
    pub fn asset(&self)  -> Result<Address, Erc20Error> {
        Ok(self.asset.get())
    }
    pub fn totalAssets(&self) -> Result<U256, Erc20Error> {
        Ok(self.totalSupply.get())
    }
}
