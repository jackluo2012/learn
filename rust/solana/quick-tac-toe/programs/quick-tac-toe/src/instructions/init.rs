use anchor_lang::prelude::*;
use anchor_spl::token::{Token,Mint};
use crate::state::program_state::*;

pub fn init(ctx: Context<Init>) -> Result<()> {
    // 创建一个新的游戏的程序状态账户
    let program_state = &mut ctx.accounts.program_state;
    program_state.bump = ctx.bumps.program_state;
    // program_state.init(ctx.bumps.program_state);
    Ok(())
}

#[derive(Accounts)]
pub struct Init<'info> {
    #[account(
        init,
        payer = payer,
        mint::decimals = 0,
        mint::authority = mint,
        seeds = [b"play_token_mint"], 
        bump
    )]
    pub mint: Account<'info, Mint>,
    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
    pub token_program: Program<'info, Token>,
    // 租金帐号
    pub rent: Sysvar<'info, Rent>,
    #[account(
        init,
        payer = payer,
        space = 8 + ProgramStateTest::INIT_SPACE,
        seeds = [b"program_state"], 
        bump
    )]
    pub program_state: Account<'info, ProgramStateTest>,
}

#[account]
#[derive(InitSpace)]
pub struct ProgramStateTest {
    pub current_version: u64,
    pub current_game_id: u64, // Use this to init next game
    pub bump: u8,
}