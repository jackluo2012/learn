
use anchor_lang::prelude::*;


use crate::{constants::{LIQUIDATION_BONUS, LIQUIDATION_THRESHOLD, MIN_HEALTH_FACTOR}, Config, MINT_DECIMALS, SEED_CONFIG_ACCOUNT, SEED_MINT_ACCOUNT};
use anchor_spl::{
    associated_token::AssociatedToken,token_interface::{self,Token2022, Mint, MintTo, TokenAccount, TokenInterface, TransferChecked}
};
#[derive(Accounts)]
pub struct InitializeConfig<'info> {
    #[account(mut)]
    // 这个将是权限人
    pub authority: Signer<'info>,
    #[account(
        init,
        payer = authority,
        space =8 +   Config::INIT_SPACE,
        // 我们整个工作区会有很多的PAD,我们不得不经常参考PDA,
        // 所以必须记住所有的种子 
        // 每个PDA都能够导出他们
        // 为了方便起见，我们将创建一个常量 文件
        //  在一个空间内，跟踪所有内容，所一些常数拉进来
        // 每当你需要派生特定的PDA时
        seeds = [SEED_CONFIG_ACCOUNT],
        bump,
    )]
    // 这个将是配置账户
    pub config_account: Account<'info, Config>,
    // 在整个稳定币项目中还需要什么
    // 我们还需要一个稳定币的mint账户
    #[account(
        init,
        payer = authority,
        mint::authority = config_account,
        mint::decimals = MINT_DECIMALS,      
        mint::freeze_authority = mint_account,  
        mint::token_program = token_program,
        seeds = [SEED_MINT_ACCOUNT],
        bump,
    )]
    // 这个将是稳定币的铸造账户
    pub mint_account: InterfaceAccount<'info, Mint>,
    pub token_program: Program<'info, Token2022>,
    pub system_program: Program<'info, System>,
}
pub fn process_initialize_config(
    ctx: Context<InitializeConfig>
) -> Result<()> {
    *ctx.accounts.config_account = Config {
        //引入权威机构的公钥
        authority: ctx.accounts.authority.key(),
        mint_account: ctx.accounts.mint_account.key(),
        // 计算清算门槛，清算奖金，最低健康因素
        liquidation_threshold: LIQUIDATION_THRESHOLD,
        liquidation_bonus: LIQUIDATION_BONUS,
        min_health_factor: MIN_HEALTH_FACTOR,
        bump: ctx.bumps.config_account,
        bump_mint_account: ctx.bumps.mint_account,
    };
    // 这个将是稳定币的铸造账户

    Ok(())
}