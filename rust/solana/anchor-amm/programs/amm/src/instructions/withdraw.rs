use anchor_lang::prelude::*;

use anchor_spl::associated_token::AssociatedToken;
use anchor_spl::token::{
    burn,
    transfer_checked,
    Burn,
    Mint,
    Token,
    TokenAccount,
    Transfer,
    TransferChecked,
};
use crate::errors::AmmError;
use crate::state::Config;
use crate::{ assert_non_zero, assert_not_expired, assert_not_locked };
use constant_product_curve::ConstantProduct;

#[derive(Accounts)]
pub struct Withdraw<'info> {
    #[account(mut)]
    pub user: Signer<'info>,
    pub mint_x: Box<Account<'info, Mint>>,
    pub mint_y: Box<Account<'info, Mint>>,
    #[account(
        mut,
        seeds = [b"lp", config.key().as_ref()],
        bump = config.mint_lp_bump
    )]
    pub mint_lp: Box<Account<'info, Mint>>,
    #[account(
        mut,
        associated_token::mint = mint_x,
        associated_token::authority = config,
    )]
    pub vault_x: Box<Account<'info, TokenAccount>>,
    #[account(
        mut,
        associated_token::mint = mint_y,
        associated_token::authority = config,
    )]
    pub vault_y: Box<Account<'info, TokenAccount>>,
    #[account(
        init_if_needed,
        payer = user,
        associated_token::mint = mint_x,
        associated_token::authority = user
    )]
    pub user_x: Box<Account<'info, TokenAccount>>,
    #[account(
        init_if_needed,
        payer = user,
        associated_token::mint = mint_y,
        associated_token::authority = user
    )]
    pub user_y: Box<Account<'info, TokenAccount>>,
    #[account(
        mut,
        associated_token::mint = mint_lp,
        associated_token::authority = user,
    )]
    pub user_lp: Box<Account<'info, TokenAccount>>,

    #[account(
        mut,
        close = user,
        has_one = mint_x,
        has_one = mint_y,
        seeds = [b"config", config.seed.to_le_bytes().as_ref()],
        bump = config.bump
    )]
    pub config: Account<'info, Config>,
    pub token_program: Program<'info, Token>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub system_program: Program<'info, System>,
}

impl<'info> Withdraw<'info> {
    pub fn withdraw(&mut self, amount: u64, min_x: u64, min_y: u64) -> Result<()> {
        require!(!self.config.locked, AmmError::PoolLocked);
        assert_non_zero!([amount, min_x, min_y]);
        assert_not_locked!(self.config.locked);

        let (x, y) = {
            let amounts = ConstantProduct::xy_withdraw_amounts_from_l(
                self.vault_x.amount,
                self.vault_y.amount,
                self.mint_lp.supply,
                amount, //amount we want to withdraw
                6
            ).map_err(AmmError::from)?; //returns the struct
            (amounts.x, amounts.y) //destructure
        };

        require!(x >= min_x && y >= min_y, AmmError::SlippageExceeded);

        self.withdraw_tokens(true, x)?;
        self.withdraw_tokens(false, y)?;
        self.burn_lp_tokens()?;

        Ok(())
    }

    pub fn withdraw_tokens(&mut self, is_x: bool, amount: u64) -> Result<()> {
        let mint_x = self.mint_x.key().to_bytes();
        let mint_y = self.mint_y.key().to_bytes();
        let seed = self.config.seed.to_le_bytes();

        let seeds = [b"config", mint_x.as_ref(), mint_y.as_ref(), seed.as_ref()];

        let signer_seeds = &[&seeds[..]];

        let (mint, decimals, vault, ata) = match is_x {
            true =>
                (
                    self.mint_x.to_account_info(),
                    self.mint_x.decimals,
                    self.vault_x.to_account_info(),
                    self.user_x.to_account_info(),
                ),
            false =>
                (
                    self.mint_y.to_account_info(),
                    self.mint_y.decimals,
                    self.vault_y.to_account_info(),
                    self.user_y.to_account_info(),
                ),
        };

        let program = self.token_program.to_account_info();

        let accounts = TransferChecked {
            from: vault,
            to: ata,
            mint,
            authority: self.config.to_account_info(),
        };

        let cpi_ctx = CpiContext::new_with_signer(program, accounts, signer_seeds);

        transfer_checked(cpi_ctx, amount, decimals);

        Ok(())
    }

    pub fn burn_lp_tokens(&mut self) -> Result<()> {
        let cpi_program = self.token_program.to_account_info();
        let accounts = Burn {
            mint: self.mint_lp.to_account_info(),
            from: self.user_lp.to_account_info(),
            authority: self.user.to_account_info(),
        };

        let cpi_ctx = CpiContext::new(cpi_program, accounts);

        burn(cpi_ctx, self.user_lp.amount);
        Ok(())
    }
}
