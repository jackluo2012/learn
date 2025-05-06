use anchor_lang::prelude::*;

declare_id!("5eef23DT6KJ62m9Lfhx85CCjhac6yvBrmwzsgG8gpfQ1");

#[program]
pub mod anchor_bac {
    use super::*;

    pub fn initialize_bac(ctx: Context<InitializeBac>) -> Result<()> {
        msg!("Greetings from: {:?}", ctx.program_id);
        Ok(())
    }
}

#[derive(Accounts)]
pub struct InitializeBac {}
