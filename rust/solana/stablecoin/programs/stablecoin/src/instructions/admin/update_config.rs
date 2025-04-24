use anchor_lang::prelude::*;
use pyth_solana_receiver_sdk::config;

use crate::{SEED_CONFIG_ACCOUNT, Config};

#[derive(Accounts)]
pub struct UpdateConfig<'info> {
    // 权威账户
    #[account(
        mut,
        seeds = [SEED_CONFIG_ACCOUNT],
        bump = config_account.bump,
    )]
    pub config_account: Account<'info, Config>,
}

pub fn process_update_config(
    ctx: Context<UpdateConfig>,    
    min_health_factor: u64,
) -> Result<()> {
    // 更新配置账户
    let config_account = &mut ctx.accounts.config_account;

    config_account.min_health_factor = min_health_factor;
    Ok(())
}