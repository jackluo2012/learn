use anchor_lang::prelude::*;

use crate::state::Config;

#[derive(Accounts)]
pub struct UpdateConfig<'info> {
    #[account(mut)]
    pub user: Signer<'info>,
    #[account(
        mut,    
        seeds=[
            b"config",
            user.key().to_bytes().as_ref(),
            config.mint_x.key().to_bytes().as_ref(),
            config.mint_y.key().to_bytes().as_ref(),
            config.seed.to_le_bytes().as_ref(),
        ],
        bump = config.bump
    )]
    pub config: Account<'info,Config>
}

impl<'info> UpdateConfig<'info> {
    pub fn lock(
        &mut self,
    ) -> Result<()> {
        self.config.locked = true;
        Ok(())
    }

    pub fn unlock(
        &mut self,
    ) -> Result<()> {
        self.config.locked = false;
        Ok(())
    }
}