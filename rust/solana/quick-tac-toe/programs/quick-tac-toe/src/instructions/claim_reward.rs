#![allow(clippy::result_large_err)]
use {
    anchor_lang::prelude::*,
    anchor_spl::{
        associated_token::AssociatedToken,
        metadata::{
            create_master_edition_v3, create_metadata_accounts_v3, CreateMasterEditionV3,
            CreateMetadataAccountsV3, Metadata,
        },
        token::{mint_to, Mint, MintTo, Token, TokenAccount},
    },
    mpl_token_metadata::{
        accounts::{Metadata as MetadataAccount, MasterEdition},
        types::DataV2
    },
};
use crate::state::player::*;
use crate::errors::TicTacToeError;

// 用户必须赢得此数量的游戏后才能领取奖励。
const CLAIM_THRESHOLD: u8 = 1;

pub fn claim_reward(ctx: Context<ClaimReward>) -> Result<()> {
    // Replace with your NFT details
    let nft_name: String = "Quick-Tac-Toe Trophy".to_string();
    let nft_symbol: String = "QTT".to_string();
    let nft_uri: String = "https://arweave.net/PkmMMr2GNK3eraWcat-pl7BwGGUQN5QLEyzDtIjbYWI".to_string();
    let player_pda = &mut ctx.accounts.player_pda;

    // 检查玩家是否赢得了足够多的游戏，且尚未领取奖励
    require!(player_pda.record.wins >= CLAIM_THRESHOLD, TicTacToeError::NotEligibleForReward);
    require!(!player_pda.reward_claimed, TicTacToeError::RewardAlreadyClaimed);

    // Cross Program Invocation (CPI)
    // Invoking the mint_to instruction on the token program
    mint_to(
        CpiContext::new(
            ctx.accounts.token_program.to_account_info(),
            MintTo {
                mint: ctx.accounts.mint_account.to_account_info(),
                to: ctx.accounts.associated_token_account.to_account_info(),
                authority: ctx.accounts.player.to_account_info(),
            },
        ),
        1,
    )?;

    // Cross Program Invocation (CPI)
    // Invoking the create_metadata_account_v3 instruction on the token metadata program
    create_metadata_accounts_v3(
        CpiContext::new(
            ctx.accounts.token_metadata_program.to_account_info(),
            CreateMetadataAccountsV3 {
                metadata: ctx.accounts.metadata_account.to_account_info(),
                mint: ctx.accounts.mint_account.to_account_info(),
                mint_authority: ctx.accounts.player.to_account_info(),
                update_authority: ctx.accounts.player.to_account_info(),
                payer: ctx.accounts.player.to_account_info(),
                system_program: ctx.accounts.system_program.to_account_info(),
                rent: ctx.accounts.rent.to_account_info(),
            },
        ),
        DataV2 {
            name: nft_name,
            symbol: nft_symbol,
            uri: nft_uri,
            seller_fee_basis_points: 0,
            creators: None,
            collection: None,
            uses: None,
        },
        false, // Is mutable
        true,  // Update authority is signer
        None,  // Collection details
    )?;

    // Cross Program Invocation (CPI)
    // Invoking the create_master_edition_v3 instruction on the token metadata program
    create_master_edition_v3(
        CpiContext::new(
            ctx.accounts.token_metadata_program.to_account_info(),
            CreateMasterEditionV3 {
                edition: ctx.accounts.edition_account.to_account_info(),
                mint: ctx.accounts.mint_account.to_account_info(),
                update_authority: ctx.accounts.player.to_account_info(),
                mint_authority: ctx.accounts.player.to_account_info(),
                payer: ctx.accounts.player.to_account_info(),
                metadata: ctx.accounts.metadata_account.to_account_info(),
                token_program: ctx.accounts.token_program.to_account_info(),
                system_program: ctx.accounts.system_program.to_account_info(),
                rent: ctx.accounts.rent.to_account_info(),
            },
        ),
        None, // Max Supply
    )?;

    player_pda.reward_claimed = true;
    Ok(())
}

#[derive(Accounts)]
pub struct ClaimReward<'info> {
    #[account(mut)]
    pub player: Signer<'info>,
    
    // Player PDA (record)
    #[account(
        mut,
        seeds = [b"player", player.key().as_ref()],
        bump = player_pda.bump
    )]
    pub player_pda: Account<'info, Player>,


    /// CHECK: Address validated using constraint
    #[account(
        mut,
        address=MetadataAccount::find_pda(&mint_account.key()).0
    )]
    pub metadata_account: UncheckedAccount<'info>,

    /// CHECK: Address validated using constraint
    #[account(
        mut,
        address=MasterEdition::find_pda(&mint_account.key()).0
    )]
    pub edition_account: UncheckedAccount<'info>,

    // Create new mint account, NFTs have 0 decimals
    #[account(
        init,
        payer = player,
        mint::decimals = 0,
        mint::authority = player.key(),
        mint::freeze_authority = player.key(),
    )]
    pub mint_account: Account<'info, Mint>,

    // Create associated token account, if needed
    // This is the account that will hold the NFT
    #[account(
        init,
        payer = player,
        associated_token::mint = mint_account,
        associated_token::authority = player,
    )]
    pub associated_token_account: Account<'info, TokenAccount>,

    pub token_program: Program<'info, Token>,
    pub token_metadata_program: Program<'info, Metadata>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub system_program: Program<'info, System>,
    pub rent: Sysvar<'info, Rent>,
}