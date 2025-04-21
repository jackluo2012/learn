use anchor_lang::prelude::*;
use instructions::*;
// 包含我们的state
mod state;
mod instructions;
mod error;
mod constants;
declare_id!("6yyF7gRjLDJnneNEj21Po7uo2S2GFXQnsgxSfUStJu2a");

#[program]
pub mod lending {
    use super::*;
    // 申明指令
    pub fn init_bank(ctx: Context<InitBank>, liquidation_threshold: u64,max_ltv: u64) -> Result<()> {
        process_init_bank(ctx, liquidation_threshold,max_ltv)

    }

    // 初始化用户
    pub fn init_user(ctx: Context<InitUser>,usdc_address: Pubkey) -> Result<()> {
        process_init_user(ctx,usdc_address)
    }

    // 用户将钱存入 银行 存款
    pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
        process_deposit(ctx, amount)
    }
    // 用户从银行提款
    pub fn withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
        process_withdraw(ctx, amount)
    }
    // 从用户进行借款
    pub fn borrow(ctx: Context<Borrow>, amount: u64) -> Result<()> {
        process_borrow(ctx, amount)
    }
    // 用户还款
    pub fn repay(ctx: Context<Repay>, amount: u64) -> Result<()> {
        process_repay(ctx, amount)
        
    }
    // 清算
    pub fn liquidate(ctx: Context<Liquidate>, amount: u64) -> Result<()> {
        process_liquidate(ctx, amount)
    }
}

// 定义程序状态 ，哪些账号需要程序保护状态
#[account]
pub struct Lending {
    pub authority: Pubkey,
    pub borrower: Pubkey,
    pub amount: u64,
    pub interest_rate: u64,
    pub duration: u64,
    pub start_time: i64,
    pub end_time: i64,
    pub is_active: bool,
}