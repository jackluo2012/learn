use anchor_lang::prelude::*;
use anchor_spl::{
    associated_token::AssociatedToken,
    token::{mint_to, Mint, Token, MintTo, TokenAccount},
};
use crate::state::player::*;

pub fn create_player(ctx: Context<CreatePlayer>) -> Result<()> {
    // 初始化玩家
    let new_player = &mut ctx.accounts.player_pda;
    new_player.init(ctx.accounts.player.key(),ctx.bumps.player_pda);

    // 铸造并分发新的游戏代币给玩家
    let signer_seeds: &[&[&[u8]]] = &[&[b"play_token_mint", &[ctx.bumps.mint]]];
    let airdrop_amount: u64 = 10;

    mint_to(
        CpiContext::new(
            ctx.accounts.token_program.to_account_info(),
            MintTo {
                mint: ctx.accounts.mint.to_account_info(),
                to: ctx.accounts.player_token_account.to_account_info(),
                authority: ctx.accounts.mint.to_account_info(),
            },
        )
        .with_signer(signer_seeds), // 使用pda 的签名
        airdrop_amount
    )?;
    new_player.airdrop_received = true;

    Ok(())
}

#[derive(Accounts)]
pub struct CreatePlayer<'info> {
    // 创建新玩家账户的用户账户
    #[account(mut)]
    pub player: Signer<'info>,
    // 创建用户的 player 的类型的PDA 的账户
    #[account(
        init,
        payer = player, 
        space = Player::calculate_account_space(), 
        seeds = [b"player", player.key().as_ref()],
        bump
    )]
    pub player_pda: Account<'info, Player>,
    // 创建的代币铸币。我们需要传入它才能铸造新的代币
    #[account(
        mut,
        seeds = [b"play_token_mint"], 
        bump
    )]
    pub mint: Account<'info, Mint>,
    // 玩家创建的代币账户
    #[account(
        init_if_needed,
        payer = player,
        associated_token::mint = mint,
        associated_token::authority = player,
    )]
    pub player_token_account: Account<'info, TokenAccount>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub token_program: Program<'info, Token>,
    pub system_program: Program<'info, System>
}