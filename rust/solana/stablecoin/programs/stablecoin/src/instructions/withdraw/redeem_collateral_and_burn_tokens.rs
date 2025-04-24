use anchor_lang::{prelude::*, solana_program::stake::instruction::withdraw};
use pyth_solana_receiver_sdk::price_update::PriceUpdateV2;

use crate::{
    deposit_sol, 
    mint_tokens, Collateral,
     Config, SEED_COLLATERAL_ACCOUNT, 
     SEED_CONFIG_ACCOUNT, 
     SEED_MINT_ACCOUNT, 
     SEED_SOL_ACCOUNT,
     
     check_health_factor,
     burn_tokens,
     withdraw_sol,
};
use anchor_spl::{
    associated_token::AssociatedToken,
    token_interface::{self,Token2022, Mint, MintTo, TokenAccount, TokenInterface, TransferChecked}
};


#[derive(Accounts)]
pub struct RedeemCollateralAndBurnTokens<'info> {
    // 存款人的账户
    #[account(
        mut,
    )]
    pub depositor: Signer<'info>,
    // 我们需要稳定币的全局配置
    pub price_update: Account<'info,PriceUpdateV2>,
    #[account(
        mut,
        seeds = [SEED_CONFIG_ACCOUNT],
        bump = config_account.bump,
        //我们需要一个约束，确保每个账户拥有正确的铸币账户
        has_one = mint_account,
    )]
    pub config_account: Box<Account<'info, Config>>,
    // 我们需要抵押品的账户
    
    //我们需要一个约束，确保每个账户拥有正确的铸币账户
    #[account(
        mut,
        seeds = [SEED_COLLATERAL_ACCOUNT, depositor.key().as_ref()],
        bump = collateral_account.bump,
        has_one = sol_account,
        has_one = token_account,       
    )]
    pub collateral_account: Account<'info, Collateral>,
    // 我们需要sol 账户
    #[account(
        mut        
    )]
    pub sol_account: SystemAccount<'info>,
    // 我们需要稳定币的铸币账户
    #[account(
        mut        
    )]
    pub mint_account: InterfaceAccount<'info, Mint>,
    // 我们需要跟踪稳定币的账户
    #[account(
        mut,        
    )]
    pub token_account: InterfaceAccount<'info, TokenAccount>,
    // 我们需要令牌程序 和系统 程序 
    pub token_program: Program<'info, Token2022>,
    pub system_program: Program<'info, System>,
}
//  提取好多抵押,燃烧好多少代币
pub fn process_redeem_collateral_and_burn_tokens(
    ctx: Context<RedeemCollateralAndBurnTokens>,
    amount_collateral: u64,
    amount_to_burn: u64,
) -> Result<()> {
    let collateral_account = &mut ctx.accounts.collateral_account;
    // 更新 抵押品的数量
    collateral_account.lamport_balance = ctx.accounts.sol_account.lamports() - amount_collateral;
    // 更新铸造的数量
    collateral_account.amount_minted -= amount_to_burn;
    // 我们会检查健康状态
    check_health_factor(
        &ctx.accounts.collateral_account,
        &ctx.accounts.config_account,
        &ctx.accounts.price_update,
    )?;
    // 我们会销毁代币 ,提取sol
    burn_tokens(
        &ctx.accounts.token_program,
        &ctx.accounts.mint_account,      
        &ctx.accounts.token_account,
        &ctx.accounts.depositor, 
        amount_to_burn,
    )?;
    // 我们会提取sol
    withdraw_sol(
        &ctx.accounts.depositor.key(),
        ctx.accounts.collateral_account.bump_sol_account,
        &ctx.accounts.system_program,
        &ctx.accounts.sol_account,
        &ctx.accounts.depositor.to_account_info(),
        amount_collateral,
    )?;


    Ok(())
}