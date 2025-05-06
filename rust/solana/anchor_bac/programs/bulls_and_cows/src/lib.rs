use anchor_lang::prelude::*;

declare_id!("5srS8MHd997JrMoefDsNFinKZpYcvHabTDXF1HU4V8yt");

#[program]
pub mod bulls_and_cows {
    use super::*;
    use std::cmp::Ordering;
    
    pub  fn guess(ctx: Context<AccountContext>, guess: u32) -> Result<()> { 
        if ctx.accounts.guessing_account.number == 0 {            
            let guessing_account = &mut ctx.accounts.guessing_account;
            guessing_account.number = generate_random_number();
        }
        // 先拿到值
        let guessing_account = &mut ctx.accounts.guessing_account;
    
        // 比较
        match guess.cmp(&guessing_account.number) {
            std::cmp::Ordering::Equal => {
                Ok(())
            }
            std::cmp::Ordering::Less => {
                err!(ErrorCode::TooSmall)
            }
            std::cmp::Ordering::Greater => {
                err!(ErrorCode::TooBig)
            }
        }
    }
}
//随机函数
fn generate_random_number() -> u32 {
    let clock = Clock::get().expect("Failed to get clock");
    (clock.unix_timestamp%10+1) as u32
}

#[account]
#[derive(InitSpace)]
pub struct GuessingAccount {
    pub number: u32
}

#[derive(Accounts)]
pub struct AccountContext<'info> {
    #[account(
        init_if_needed,
        payer = payer, 
        space = 8 + GuessingAccount::INIT_SPACE,
        seeds = [b"guessing pda".as_ref()], 
        bump
    )]
    pub guessing_account: Account<'info, GuessingAccount>,
    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[error_code]
pub enum ErrorCode {
    #[msg("The guessing account is not initialized")]
    NotInitialized,
    #[msg("Too small")]
    TooSmall,
    #[msg("Too big")]
    TooBig,
}
