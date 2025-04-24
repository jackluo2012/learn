use anchor_lang::{prelude::*};
use anchor_spl::token_interface::{Mint, TokenAccount,Token2022};
use pyth_solana_receiver_sdk::price_update::PriceUpdateV2;

use crate::{
    calculate_health_factor, CustomError,burn_tokens,get_lamports_from_usd, withdraw_sol, Collateral, Config, SEED_CONFIG_ACCOUNT
};

// 清算指令
// 我们需要的账户
#[derive(Accounts)]
pub struct Liquidate<'info> {
    // 清算人
    #[account(mut)]
    pub liquidator: Signer<'info>,
    // 价格喂价账户
    pub price_update: Account<'info,PriceUpdateV2>,
    // 我们需要稳定币的全局配置
    #[account(
        mut,
        seeds = [SEED_CONFIG_ACCOUNT],
        bump = config_account.bump,
        //我们需要一个约束，确保每个账户拥有正确的铸币账户
        has_one = mint_account,
    )]
    pub config_account: Box<Account<'info, Config>>,
    // 我们需要抵押品的账户
    #[account(
        mut,
        has_one = sol_account,
    )]
    pub collateral_account: Box<Account<'info, Collateral>>,
    
    // 我们需要稳定币的铸币账户
    #[account(
        mut,
    )]
    pub mint_account: InterfaceAccount<'info, Mint>,    
    // 我们需要sol 账户
    #[account(
        mut,
    )]
    pub sol_account: SystemAccount<'info>,
    // 清算人的代币账户
    #[account(
        mut,
        associated_token::mint = mint_account,
        associated_token::authority = liquidator,
        associated_token::token_program = token_program,
    )]
    pub token_account: InterfaceAccount<'info, TokenAccount>,
    // 系统程序
    pub token_program: Program<'info,Token2022>,
    pub system_program: Program<'info,System>,
}
// 执行清算程序
pub fn process_liquidate(ctx: Context<Liquidate>, amount_to_burn: u64) -> Result<()> {
    // 在执行清算之前,我们得确定 账户不是健康的,是可以被清算的
    let health_factor = calculate_health_factor(
        &ctx.accounts.collateral_account, 
        &ctx.accounts.config_account,
        &ctx.accounts.price_update,
    )?;
    require!(
        health_factor < ctx.accounts.config_account.min_health_factor, 
        CustomError::AboveMinHealthFactor
    );

    let lamports = get_lamports_from_usd(
        &ctx.accounts.price_update, &amount_to_burn)?;
    
    // 我们计算一下清算奖金是多少,这些将转给清算人
    let liquidation_bonus = lamports * ctx.accounts.config_account.liquidation_bonus / 100;
    // 清算的数量是,要清算的稳定币数量加上奖金,将这笔给清算人
    let amount_to_liquidate = lamports + liquidation_bonus;
    // 因此,当我们清算时,我们希望能够提取,SOL从账户中,我们希望能够销毁代币
    // 然后只需更新抵押账户状态 
    //  我们先撤回sol
    withdraw_sol(
        &ctx.accounts.collateral_account.depositor, 
        ctx.accounts.collateral_account.bump_sol_account, 
        &ctx.accounts.system_program, 
        &ctx.accounts.sol_account, 
        &ctx.accounts.liquidator.to_account_info(), 
        amount_to_liquidate
    )?;
    //销毁稳定币
    burn_tokens(
        &ctx.accounts.token_program,
        &ctx.accounts.mint_account,
        &ctx.accounts.token_account,
        &ctx.accounts.liquidator,
        amount_to_liquidate,
        
    )?;
    // 我们将更新抵押品账户的信息
    let collateral_account= &mut ctx.accounts.collateral_account;
    // 已经清算过了,所以直接 就是值 
    collateral_account.lamport_balance = ctx.accounts.sol_account.lamports();
    // 减去铸造的数量
    collateral_account.amount_minted -= amount_to_burn;

    // 再次计算一下 健康因子
    calculate_health_factor(
        collateral_account,
        &ctx.accounts.config_account,
        &ctx.accounts.price_update,
    )?;



    Ok(())
}