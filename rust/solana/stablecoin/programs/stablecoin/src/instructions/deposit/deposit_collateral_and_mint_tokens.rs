use anchor_lang::prelude::*;
use pyth_solana_receiver_sdk::price_update::PriceUpdateV2;

use crate::{
    deposit_sol, 
    mint_tokens, Collateral,
     Config, SEED_COLLATERAL_ACCOUNT, 
     SEED_CONFIG_ACCOUNT, 
     SEED_MINT_ACCOUNT, 
     SEED_SOL_ACCOUNT,
     calculate_health_factor,
};
use anchor_spl::{
    associated_token::AssociatedToken,
    token_interface::{self,Token2022, Mint, MintTo, TokenAccount, TokenInterface, TransferChecked}
};
// 我们正在处理存款和铸造稳定币的指令
// 所以我们需要持有这些代币的账户

// 存储抵押品并铸造稳定币的指令
#[derive(Accounts)]
pub struct DepositCollateralAndMintTokens<'info> {
    // 存款人的账户
    #[account(
        mut,
   )]
    pub depositor: Signer<'info>,
    // 我们需要稳定币的全局配置
    #[account(
        mut,
        seeds = [SEED_CONFIG_ACCOUNT],
        bump = config_account.bump,
        //我们需要一个约束，确保每个账户拥有正确的铸币账户
        has_one = mint_account,
    )]
    pub config_account: Box<Account<'info, Config>>,
    //我们需要一个约束，确保每个账户拥有正确的铸币账户
    #[account(
        mut,
    )]
    pub mint_account: InterfaceAccount<'info, Mint>,
    // 我们需要跟踪抵押品，所以我们要存入 抵押品的账户
    // 所以我们可以根据需要更新状态
    #[account(
        init_if_needed,
        payer = depositor,
        space = 8 + Collateral::INIT_SPACE,
        // 这个是针对特定用户的，所以还要 存款人的密钥
        seeds = [SEED_COLLATERAL_ACCOUNT, depositor.key().as_ref()],
        bump,
    )]
    pub collateral_account: Account<'info, Collateral>,
    // 我们需要两个关联的令牌账户，一个是sol,一是稳定币
    #[account(
        mut,
        // 这个是存款人的稳定币账户，作为PDA
        seeds = [SEED_SOL_ACCOUNT, depositor.key().as_ref()],
        bump,
    )]
    pub sol_account: SystemAccount<'info>,
    // 我们还需要关联的代币账户，用于稳定币的铸造
    #[account(
        init_if_needed,
        payer = depositor,
        associated_token::mint = mint_account,
        associated_token::authority = depositor,
        associated_token::token_program = token_program,
    )]
    pub token_account: InterfaceAccount<'info, TokenAccount>,
    pub token_program: Program<'info, Token2022>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    // 我们还需要一个系统程序来处理sol的存款

    pub system_program: Program<'info, System>,
    // 获取市场价格的pyth程序
    // 我们需要一个pyth程序来获取市场价格
    pub price_update: Account<'info,PriceUpdateV2>,

}

// amount_sol 是存入的sol的数量
// amount_mint 是铸造的稳定币的数量
pub fn process_deposit_collateral_and_mint_tokens(
    ctx: Context<DepositCollateralAndMintTokens>,
    amount_collateral: u64,
    amount_to_mint: u64,
) -> Result<()> {
    // 提取抵押账户，根据金额更新 账户状态 
    // 我们存入 的抵押品以及我们铸造的代币数量
    let collateral_account = &mut ctx.accounts.collateral_account;
    // 更新 抵押品的数量 和铸造的代币数量
    collateral_account.lamport_balance = ctx.accounts.sol_account.lamports() + amount_collateral;
    collateral_account.amount_minted += amount_to_mint;
    // 检查账户是否初始化
    if !collateral_account.is_initialized {
        collateral_account.is_initialized = true;
        //存款人账户的密钥
        collateral_account.depositor = ctx.accounts.depositor.key();
        // 设置sol_account的密钥
        collateral_account.sol_account = ctx.accounts.sol_account.key();
        // 设置token_account的密钥
        collateral_account.token_account = ctx.accounts.token_account.key();
        // 设置bumps
        collateral_account.bump = ctx.bumps.collateral_account;
        //设置sol_account的bumps
        collateral_account.bump_sol_account = ctx.bumps.sol_account;
    }
    // 在我们实际 执行铸造代币的存款之前,我们先检查健康状态
    calculate_health_factor(
        &ctx.accounts.collateral_account,
        &ctx.accounts.config_account,
        &ctx.accounts.price_update,
    )?;
    
    
    // 现在我们要存入sol
    deposit_sol(
        &&ctx.accounts.depositor,
        &ctx.accounts.sol_account,
        &ctx.accounts.system_program,
        amount_collateral,
    )?;
    mint_tokens(
        &ctx.accounts.mint_account,
        &ctx.accounts.token_account,
        &ctx.accounts.token_program,
        amount_to_mint,
        ctx.accounts.config_account.bump_mint_account,
    )?;



    Ok(())
}