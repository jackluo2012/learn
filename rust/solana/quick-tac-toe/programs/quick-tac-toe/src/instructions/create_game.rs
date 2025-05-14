use anchor_lang::prelude::*;
use anchor_spl::token::{burn, Burn, Mint, Token, TokenAccount};
use crate::state::game::*;
use crate::state::player::*;
use crate::state::program_state::*;

pub fn create_game(ctx: Context<CreateGame>, game_id: u64) -> Result<()> {
    // 玩游戏要支付游戏费，所以我们直接销毁游戏费
    // Burn Payment Token
    let play_fee: u64 = 1;
    let cpi_accounts = Burn {
        mint: ctx.accounts.mint.to_account_info(),
        from: ctx.accounts.player_token_account.to_account_info(),
        authority: ctx.accounts.player_x.to_account_info(),
    };
    let cpi_program = ctx.accounts.token_program.to_account_info();
    let cpi_ctx = CpiContext::new(cpi_program, cpi_accounts);
    burn(cpi_ctx, play_fee)?;

    // Create Game
    let game = &mut ctx.accounts.game;
    let program_state = &mut ctx.accounts.program_state;
    game.create(
        ctx.accounts.player_x.key(),
        ctx.bumps.game,
        program_state.current_game_id,
    );

    // 更新程序状态以反映游戏计数的增加

    program_state.increment_game_id();

    Ok(())
}

#[derive(Accounts)]
#[instruction(game_id: u64)]
pub struct CreateGame<'info> {
    // 一局游戏 记录 Game Account
    #[account(
        init,
        payer = player_x, 
        space = Game::calculate_account_space(), 
        seeds = [
            b"new_game",
            program_state.current_game_id.to_string().as_bytes(),            
        ], 
        bump
    )]
    pub game: Account<'info, Game>,
    #[account(
        mut,
        seeds = [b"program_state"], 
        bump = program_state.bump
    )]
    pub program_state: Account<'info, ProgramState>,
    // Player/Signer Wallet
    #[account(mut)]
    pub player_x: Signer<'info>,

    // Player PDA (record)
    #[account(
        seeds = [b"player", player_x.key().as_ref()],
        bump = player_pda.bump
    )]
    pub player_pda: Account<'info, Player>,

    // Fee Mint
    #[account(
        mut,
        seeds = [b"play_token_mint"], 
        bump
    )]
    pub mint: Account<'info, Mint>,

    // Players Token Account
    #[account(
        mut,
        associated_token::mint = mint,
        associated_token::authority = player_x,
    )]
    pub player_token_account: Account<'info, TokenAccount>,
    
    pub token_program: Program<'info, Token>,
    pub system_program: Program<'info, System>,

    
}