use anchor_lang::prelude::*;
use anchor_spl::token::{burn, Burn, Mint, Token, TokenAccount};
use crate::errors::TicTacToeError;
use crate::state::game::*;
use crate::state::player::*;

pub fn join_game(ctx: Context<JoinGame>) -> Result<()> {
    let game = &mut ctx.accounts.game;
    let new_player = &ctx.accounts.player_o;

    // 确保不是同一个玩家
    require!(
        game.player_x != new_player.key(),
        TicTacToeError::InvalidPlayer
    );
    // 确保游戏还没有开始
    require!(
        game.state == GameState::NotStarted,
        TicTacToeError::GameAlreadyStarted
    );

    // 玩销毁游戏费
    let play_fee: u64 = 1;
    let cpi_accounts = Burn {
        mint: ctx.accounts.mint.to_account_info(),
        from: ctx.accounts.player_token_account.to_account_info(),
        authority: ctx.accounts.player_o.to_account_info(),
    };
    let cpi_program = ctx.accounts.token_program.to_account_info();
    let cpi_ctx = CpiContext::new(cpi_program, cpi_accounts);
    burn(cpi_ctx, play_fee)?;

    // 玩家加入游戏
    game.start(new_player.key());
    Ok(())
}

#[derive(Accounts)]
pub struct JoinGame<'info> {
    // Game Account
    #[account(
        mut,
        seeds = [
            b"new_game",
            game.id.to_string().as_bytes(),            
        ], 
        bump = game.bump
    )]
    pub game: Account<'info, Game>,

    // Player/Signer Wallet
    #[account(mut)]
    pub player_o: Signer<'info>,


    // Player PDA (record)
    #[account(
        seeds = [b"player", player_o.key().as_ref()],
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
        associated_token::authority = player_o,
    )]
    pub player_token_account: Account<'info, TokenAccount>,

    pub token_program: Program<'info, Token>,
    pub system_program: Program<'info, System>,
}