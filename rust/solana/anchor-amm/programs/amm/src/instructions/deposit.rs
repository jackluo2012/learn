use anchor_lang::prelude::*;
use anchor_spl::{
    associated_token::AssociatedToken,
    token_interface::{
        mint_to,
        transfer_checked,
        Mint,
        MintTo,
        TokenAccount,
        TokenInterface,
        TransferChecked,
    },
};

use constant_product_curve;

use crate::errors::AmmError;
use crate::state::Config;
use crate::{ assert_non_zero, assert_not_expired, assert_not_locked };

#[derive(Accounts)]
#[instruction(seed: u64)]
pub struct Deposit<'info> {
    #[account(mut)]
    pub provider: Signer<'info>,
    pub mint_x: Box<InterfaceAccount<'info, Mint>>,
    pub mint_y: Box<InterfaceAccount<'info, Mint>>,
    #[account(
        mut,
        seeds = [b"lp", config.key().as_ref()],
        bump=config.mint_lp_bump,
        mint::authority=config,
        mint::decimals=6
    )]
    pub mint_lp: Box<InterfaceAccount<'info, Mint>>,

    #[account(
        mut,
        associated_token::mint = mint_x,
        associated_token::authority = provider
    )]
    pub provider_ata_x: Box<InterfaceAccount<'info, TokenAccount>>,
    #[account(
        mut,
        associated_token::mint = mint_y,
        associated_token::authority = provider
    )]
    pub provider_ata_y: Box<InterfaceAccount<'info, TokenAccount>>,
    #[account(
        init_if_needed,
        payer = provider,
        associated_token::mint = mint_lp,
        associated_token::authority = provider
    )]
    pub provider_ata_lp: Box<InterfaceAccount<'info, TokenAccount>>,

    #[account(
        init_if_needed,
        payer = provider,
        associated_token::mint = mint_x,
        associated_token::authority = config
    )]
    pub vault_x: Box<InterfaceAccount<'info, TokenAccount>>,
    #[account(
        init_if_needed,
        payer = provider,
        associated_token::mint = mint_y,
        associated_token::authority = config
    )]
    pub vault_y: Box<InterfaceAccount<'info, TokenAccount>>,

    #[account(
        mut,
        seeds = [
            b"config",
            mint_x.key().to_bytes().as_ref(),
            mint_y.key().to_bytes().as_ref(),
            seed.to_le_bytes().as_ref(),
        ],
        bump = config.bump
    )]
    pub config: Account<'info, Config>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub token_program: Interface<'info, TokenInterface>,
    pub system_program: Program<'info, System>,
}

impl<'info> Deposit<'info> {
    pub fn deposit(&mut self, amount: u64, max_x: u64, max_y: u64, expiration: i64) -> Result<()> {
        assert_non_zero!([amount, max_x, max_y]);
        assert_not_locked!(self.config.locked);
        assert_not_expired!(expiration);

        let (x, y) = match self.vault_x.amount + self.vault_y.amount + self.mint_lp.supply == 0 {
            true => (max_x, max_y),
            false => {
                let amounts = constant_product_curve::ConstantProduct
                    ::xy_deposit_amounts_from_l(
                        max_x,
                        max_y,
                        self.mint_lp.supply,
                        amount,
                        self.mint_lp.decimals as u32
                    )
                    .map_err(AmmError::from)?;
                (amounts.x, amounts.y)
            }
        };

        require!(x <= max_x && y <= max_y, AmmError::SlippageExceeded);
        self.deposit_tokens(x, true)?;
        self.deposit_tokens(y, false)?;
        self.mint_lp_tokens(amount)
    }

    pub fn deposit_tokens(&mut self, amount: u64, is_x: bool) -> Result<()> {
        let (mint, provider_ata, vault, decimals) = match is_x {
            true =>
                (
                    self.mint_x.to_account_info(),
                    self.provider_ata_x.to_account_info(),
                    self.vault_x.to_account_info(),
                    self.mint_x.decimals,
                ),
            false =>
                (
                    self.mint_y.to_account_info(),
                    self.provider_ata_y.to_account_info(),
                    self.vault_y.to_account_info(),
                    self.mint_y.decimals,
                ),
        };
        let accounts = TransferChecked {
            from: provider_ata,
            to: vault,
            mint,
            authority: self.provider.to_account_info(),
        };
        let ctx = CpiContext::new(self.token_program.to_account_info(), accounts);

        transfer_checked(ctx, amount, decimals)?;
        Ok(())
    }

    pub fn mint_lp_tokens(&mut self, amount: u64) -> Result<()> {
        let accounts = MintTo {
            mint: self.mint_lp.to_account_info(),
            to: self.provider_ata_lp.to_account_info(),
            authority: self.config.to_account_info(),
        };

        let mint_y = self.mint_y.key().to_bytes();
        let mint_x = self.mint_x.key().to_bytes();
        let seed = self.config.seed.to_le_bytes();

        //if adoption a PDA just for singing change these seeds
        let seeds = [b"config", mint_x.as_ref(), mint_y.as_ref(), seed.as_ref()];
        let signer_seeds = &[&seeds[..]];

        let ctx = CpiContext::new_with_signer(
            self.token_program.to_account_info(),
            accounts,
            signer_seeds
        );
        mint_to(ctx, amount)?;

        Ok(())
    }
}

/* 
//-------------------- initialize.rs --------------------//
3 - Initialize Vault X Token Account
4 - Initialize Vault Y Token Account
5 - Initialize Maker ATA X Token Account
5 - Initialize Maker ATA Y Token Account
6 - Initialize Maker ATA LP Token Account
7 - Deposit Tokens
8 - Mint LP Tokens
*/
