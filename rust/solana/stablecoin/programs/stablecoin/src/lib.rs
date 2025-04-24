use anchor_lang::prelude::*;

use state::*;
mod state;
use constants::*;
mod constants;
use instructions::*;
mod instructions;
use error::*;
mod error;

declare_id!("4hFadtCXRJbNoyjqmKYTt1fvKmWJxgYsLYUBxfoMqhLt");

#[program]
pub mod stablecoin {
    use super::*;

    pub fn initialize_config(
        ctx: Context<InitializeConfig>
    ) -> Result<()> {
        process_initialize_config(ctx)
    }
    // 更新配置账户
    pub fn update_config(
        ctx: Context<UpdateConfig>,        
        min_health_factor: u64,
    ) -> Result<()> {
        process_update_config(
            ctx,            
            min_health_factor,
        )
    }

    // 存入抵押品并铸造代币
    // 我们已经初始化了配置,创建了配置账户
    // 我们能添加更新,配置的指令,存入抵押品,铸造代币

    pub fn deposit_collateral_and_mint_tokens(
        ctx: Context<DepositCollateralAndMintTokens>,
        amount_collateral: u64,
        amount_to_mint: u64,
    ) -> Result<()> {
        process_deposit_collateral_and_mint_tokens(
            ctx,
            amount_collateral,
            amount_to_mint,
        )
    }
    // 提取抵押品 并销毁代币
    pub fn redeem_collateral_and_burn_tokens(
        ctx: Context<RedeemCollateralAndBurnTokens>,
        amount_collateral: u64,
        amount_to_burn: u64,
    ) -> Result<()> {
        process_redeem_collateral_and_burn_tokens(ctx,amount_collateral,amount_to_burn)
    }
    // 清算
    pub fn liquidate(
        ctx: Context<Liquidate>,
        amount_to_burn: u64,
    ) -> Result<()> {
        process_liquidate(ctx,amount_to_burn)
    }
}

#[derive(Accounts)]
pub struct Initialize {}
