#![allow(clippy::result_large_err)]

use anchor_lang::prelude::*;

declare_id!("coUnmi3oBUtwtd9fjeAvSsJssXh5A5xyPbhpewyzRVF");

#[program]
pub mod crudapp {
    use super::*;

  pub fn close(_ctx: Context<CloseCrudapp>) -> Result<()> {
    Ok(())
  }

  pub fn decrement(ctx: Context<Update>) -> Result<()> {
    ctx.accounts.crudapp.count = ctx.accounts.crudapp.count.checked_sub(1).unwrap();
    Ok(())
  }

  pub fn increment(ctx: Context<Update>) -> Result<()> {
    ctx.accounts.crudapp.count = ctx.accounts.crudapp.count.checked_add(1).unwrap();
    Ok(())
  }

  pub fn initialize(_ctx: Context<InitializeCrudapp>) -> Result<()> {
    Ok(())
  }

  pub fn set(ctx: Context<Update>, value: u8) -> Result<()> {
    ctx.accounts.crudapp.count = value.clone();
    Ok(())
  }
}

#[derive(Accounts)]
pub struct InitializeCrudapp<'info> {
  #[account(mut)]
  pub payer: Signer<'info>,

  #[account(
  init,
  space = 8 + Crudapp::INIT_SPACE,
  payer = payer
  )]
  pub crudapp: Account<'info, Crudapp>,
  pub system_program: Program<'info, System>,
}
#[derive(Accounts)]
pub struct CloseCrudapp<'info> {
  #[account(mut)]
  pub payer: Signer<'info>,

  #[account(
  mut,
  close = payer, // close account and return lamports to payer
  )]
  pub crudapp: Account<'info, Crudapp>,
}

#[derive(Accounts)]
pub struct Update<'info> {
  #[account(mut)]
  pub crudapp: Account<'info, Crudapp>,
}

#[account]
#[derive(InitSpace)]
pub struct Crudapp {
  count: u8,
}
