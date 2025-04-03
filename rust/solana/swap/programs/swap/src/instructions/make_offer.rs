use anchor_lang::prelude::*;
use anchor_spl::{
    associated_token::AssociatedToken,
    token::{Mint,TokenAccount}, token_interface::TokenInterface,
};

use crate::{Offer, ANCHOR_DISCRIMINATOR_LEN};

use crate::instructions::shared::transfer_tokens;

#[derive(Accounts)]
#[instruction(id: u64)]
pub struct MakeOffer<'info> {
    #[account(mut)]
    pub maker: Signer<'info>,

    #[account(mint::token_program = token_program)]
    pub token_mint_a: InterfaceAccount<'info, Mint>,

    #[account(mint::token_program = token_program)]
    pub token_mint_b: InterfaceAccount<'info, Mint>,

    #[account(
        mut,
        associated_token::mint = token_mint_a,
        associated_token::authority = maker,
        associated_token::token_program = token_program,
    )]
    pub maker_token_account_a: InterfaceAccount<'info, TokenAccount>,

    #[account(
        init,
        payer = maker,
        space = ANCHOR_DISCRIMINATOR_LEN + Offer::INIT_SPACE,
        seeds = [b"offer", maker.key().as_ref(), id.to_le_bytes().as_ref()],
        bump,
    )]
    pub offer: Account<'info, Offer>,

    #[account(
        mut,
        associated_token::mint = token_mint_a,
        associated_token::authority = offer,
        associated_token::token_program = token_program,
    )]
    pub vault: InterfaceAccount<'info, TokenAccount>,

    pub token_program: Program<'info, TokenInterface>,
    pub system_program: Program<'info, System>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub rent: Sysvar<'info, Rent>,
}

pub fn send_offered_tokens_to_vault(ctx: &Context<MakeOffer>,token_a_offered_amount:u64) -> Result<()> {
    
    transfer_tokens(&ctx.accounts.maker_token_account_a, 
                &ctx.accounts.vault, 
                token_a_offered_amount, 
                &ctx.accounts.token_mint_a, 
                &ctx.accounts.maker, 
                &ctx.accounts.token_program
    )

    
}

pub fn save_offer(ctx: &Context<MakeOffer>,id:u64,token_b_wanted_amount:u64)->Result<()>{
    let offer = &mut ctx.accounts.offer;
    offer.id = id;
    offer.maker = ctx.accounts.maker.key();
    offer.token_mint_a = ctx.accounts.token_minit_a.key();
    offer.token_mint_b = ctx.accounts.token_minit_b.key();
    offer.token_b_wanted_amount = token_b_wanted_amount;
    offer.bump = *ctx.bumps.get("offer").unwrap();
    Ok(())
}