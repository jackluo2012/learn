use anchor_lang::prelude::*;
use anchor_spl::{
    associated_token::AssociatedToken,
    token_interface::{ Mint, TokenAccount, TokenInterface },
};

use crate::state::Config;

#[derive(Accounts)]
#[instruction(seed: u64)]
pub struct Initialize<'info> {
    #[account(mut)]
    pub maker: Signer<'info>,

    pub mint_x: Box<InterfaceAccount<'info, Mint>>,
    pub mint_y: Box<InterfaceAccount<'info, Mint>>,

    #[account(
        init,
        payer = maker,
        mint::authority = config,
        mint::decimals = 6,
        mint::token_program = token_program,
        seeds = [b"mint", config.key().as_ref()],
        bump
    )]
    pub mint_lp: Box<InterfaceAccount<'info, Mint>>,

    #[account(
        init,
        payer = maker,
        space = 8 + Config::INIT_SPACE,
        //this should have a maker in the seeds and the seed saved in the config
        seeds = [
            b"config",
            mint_x.key().as_ref(),
            mint_y.key().as_ref(),
            seed.to_le_bytes().as_ref(),
        ],
        bump
    )]
    pub config: Box<Account<'info, Config>>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub token_program: Interface<'info, TokenInterface>,
    pub system_program: Program<'info, System>,
}

impl<'info> Initialize<'info> {
    pub fn init_config(&mut self, seed: u64, fee: u16, bump: u8, lp_bump: u8) -> Result<()> {
        self.config.set_inner(Config {
            mint_x: self.mint_x.key(),
            mint_y: self.mint_y.key(),
            bump,
            mint_lp_bump: lp_bump,
            seed,
            fee,
            locked: false,
        });
        Ok(())
    }
}

/*
//-------------------- initialize.rs --------------------//
1- Initialize Mint LP Token
2- Initialize Config Account
*/
