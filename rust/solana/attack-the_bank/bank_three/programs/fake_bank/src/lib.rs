use anchor_lang::prelude::*;
use anchor_lang::system_program::{transfer, Transfer};

declare_id!("BQNDzPZTJqfcGfXMgHNBiCp2t6Y1ZnR53UwaYXRfZ2E");

#[program]
pub mod fake_bank  {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>, vault_address: Pubkey) -> Result<()> {
        *ctx.accounts.bank = Bank {
            authority: ctx.accounts.fake_authority.key(),
            vault: vault_address,
            is_initialized: true,
        };
        msg!("{:#?}", ctx.accounts.bank);
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(mut)]
    pub fake_authority: Signer<'info>,
    #[account(
        init_if_needed,
        payer = fake_authority,
        space = 8 + Bank::INIT_SPACE,
        seeds = [b"bank"],
        bump,
    )]
    pub bank: Account<'info, Bank>,
    pub system_program: Program<'info, System>,
}

#[account]
#[derive(InitSpace, Debug)]
pub struct Bank {
    pub authority: Pubkey,
    pub vault: Pubkey,
    pub is_initialized: bool,
}