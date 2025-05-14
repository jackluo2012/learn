use anchor_lang::prelude::*;
use crate::errors::TicTacToeError;
use crate::state::game::*;
use crate::state::player::*;

pub fn play(ctx: Context<Play>, square: Square) -> Result<()> {
    let game = &mut ctx.accounts.game;
    let player = &ctx.accounts.player;
    let player_record = &mut ctx.accounts.player_record;
    let other_player_record = &mut ctx.accounts.other_player_record;

    require_keys_eq!(
        game.current_player(),
        player.key(),
        TicTacToeError::NotPlayersTurn
    );
    
    require_keys_eq!(
        game.other_player_pda(),
        other_player_record.key(),
        TicTacToeError::InvalidPlayer
    );

    require!(
        game.is_active(),
        TicTacToeError::GameNotActive
    );

    game.play(&square, player_record, other_player_record)
}

#[derive(Accounts)]
pub struct Play<'info> {
    // Player/Signer Wallet
    #[account(mut)]
    pub player: Signer<'info>,

    // Player PDA (record)
    #[account(
        mut,
        seeds = [b"player", player.key().as_ref()],
        bump = player_record.bump
    )]
    pub player_record: Account<'info, Player>,

    // We verify this inside program.
    #[account(mut)]
    pub other_player_record: Account<'info, Player>,

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

    pub system_program: Program<'info, System>,
}