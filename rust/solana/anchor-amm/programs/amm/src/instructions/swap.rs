use anchor_lang::prelude::*;
use anchor_spl::{
    associated_token::AssociatedToken,
    token_interface::{ Mint, TokenAccount, TokenInterface, TransferChecked, transfer_checked },
};
use constant_product_curve::{ ConstantProduct, LiquidityPair };

use crate::state::Config;
use crate::errors::AmmError;

#[derive(Accounts)]
pub struct Swap<'info> {
    #[account(mut)]
    pub user: Signer<'info>,

    #[account(
        seeds = [b"lp", config.key().as_ref()],
        bump = config.mint_lp_bump,
        mint::authority = config,
        mint::decimals = 6
    )]
    pub mint_lp: Box<InterfaceAccount<'info, Mint>>,

    pub mint_x: InterfaceAccount<'info, Mint>,
    pub mint_y: InterfaceAccount<'info, Mint>,

    #[account(
        init_if_needed,
        payer = user,
        associated_token::authority = user,
        associated_token::mint = mint_y
    )]
    pub user_ata_x: InterfaceAccount<'info, TokenAccount>,
    #[account(
        init_if_needed,
        payer = user,
        associated_token::authority = user,
        associated_token::mint = mint_x
    )]
    pub user_ata_y: InterfaceAccount<'info, TokenAccount>,

    #[account(associated_token::mint = mint_x, associated_token::authority = config)]
    pub vault_x: InterfaceAccount<'info, TokenAccount>,
    #[account(associated_token::mint = mint_y, associated_token::authority = config)]
    pub vault_y: InterfaceAccount<'info, TokenAccount>,

    #[account(
        mut,
        seeds = [
            b"config",
            mint_x.key().to_bytes().as_ref(),
            mint_y.key().to_bytes().as_ref(),
            config.seed.to_le_bytes().as_ref(),
        ],
        bump = config.bump
    )]
    pub config: Account<'info, Config>,

    pub associated_token_program: Program<'info, AssociatedToken>,
    pub token_program: Interface<'info, TokenInterface>,
    pub system_program: Program<'info, System>,
}

impl<'info> Swap<'info> {
    pub fn swap(&mut self, is_x: bool, amount: u64, min: u64) -> Result<()> {
        let mut curve = ConstantProduct::init(
            self.vault_x.amount,
            self.vault_y.amount,
            self.mint_lp.supply,
            self.config.fee,
            None
        ).map_err(AmmError::from)?;

        let p = match is_x {
            true => LiquidityPair::X,
            false => LiquidityPair::Y,
        };

        let res = curve.swap(p, amount, min).map_err(AmmError::from)?;

        self.deposit_tokens(res.deposit, is_x)?;
        self.withdraw_tokens(res.withdraw, is_x)?;
        Ok(())
    }

    pub fn deposit_tokens(&mut self, amount: u64, is_x: bool) -> Result<()> {
        let (mint, user_ata, vault, decimals) = match is_x {
            true =>
                (
                    self.mint_x.to_account_info(),
                    self.user_ata_x.to_account_info(),
                    self.vault_x.to_account_info(),
                    self.mint_x.decimals,
                ),
            false =>
                (
                    self.mint_y.to_account_info(),
                    self.user_ata_y.to_account_info(),
                    self.vault_y.to_account_info(),
                    self.mint_y.decimals,
                ),
        };
        let accounts = TransferChecked {
            from: user_ata,
            to: vault,
            mint,
            authority: self.user.to_account_info(),
        };
        let ctx = CpiContext::new(self.token_program.to_account_info(), accounts);

        transfer_checked(ctx, amount, decimals)?;
        Ok(())
    }

    pub fn withdraw_tokens(&mut self, amount: u64, is_x: bool) -> Result<()> {
        let (mint, user_ata, vault, decimals) = match is_x {
            true =>
                (
                    self.mint_x.to_account_info(),
                    self.user_ata_x.to_account_info(),
                    self.vault_x.to_account_info(),
                    self.mint_x.decimals,
                ),
            false =>
                (
                    self.mint_y.to_account_info(),
                    self.user_ata_y.to_account_info(),
                    self.vault_y.to_account_info(),
                    self.mint_y.decimals,
                ),
        };
        let accounts = TransferChecked {
            to: user_ata,
            from: vault,
            mint,
            authority: self.config.to_account_info(),
        };

        let mint_x = self.mint_x.key().to_bytes();
        let mint_y = self.mint_y.key().to_bytes();
        let seed = self.config.seed.to_le_bytes();

        let seeds = [b"config", mint_x.as_ref(), mint_y.as_ref(), seed.as_ref()];

        let signer_seeds = &[&seeds[..]];

        let ctx = CpiContext::new_with_signer(
            self.token_program.to_account_info(),
            accounts,
            signer_seeds
        );

        transfer_checked(ctx, amount, decimals)?;
        Ok(())
    }
}
