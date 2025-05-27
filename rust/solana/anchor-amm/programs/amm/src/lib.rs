pub mod constants;
pub mod errors;
pub mod instructions;
pub mod state;
pub mod helpers;

use anchor_lang::prelude::*;

pub use constants::*;
pub use instructions::*;
pub use state::*;
pub use helpers::*;

declare_id!("HGitkDvzY7TVWCPPEfTMeGRKpSBu7b4MmerrPpr85q4e");

#[program]
pub mod amm {
    use super::*;

    // Ensures initialization of config, LP mint account, vault_x and vault_y accounts, maker_ata_x, maker_ata_y and maker_ata_lp accounts
    pub fn initialize(
        ctx: Context<Initialize>,
        seed: u64,
        fee: u16,
        authority: Option<Pubkey>
    ) -> Result<()> {
        ctx.accounts.init_config(seed, fee, ctx.bumps.config, ctx.bumps.mint_lp)?;
        Ok(())
    }

    // Add liquidity to mint LP tokens
    pub fn deposit(
        ctx: Context<Deposit>,
        amount: u64, // amount of LP token to claim
        max_x: u64, // max amount of X we are willing to deposit
        max_y: u64, // max amount of Y we are willing to deposit
        expiration: i64
    ) -> Result<()> {
        ctx.accounts.deposit(amount, max_x, max_y, expiration)?;
        Ok(())
    }

    // // Burn LP tokens to withdraw liquidity
    // pub fn withdraw(ctx: Context<Withdraw>, amount: u64, min_x: u64, min_y: u64) -> Result<()> {
    //     // burn_lp_token(amount)?;
    //     // withdraw_tokens(amount)
    //     Ok(())
    // }

    pub fn swap(ctx: Context<Swap>, is_x: bool, amount: u64, min_receive: u64) -> Result<()> {
        ctx.accounts.swap(is_x, amount, min_receive)?;
        Ok(())
    }
}
