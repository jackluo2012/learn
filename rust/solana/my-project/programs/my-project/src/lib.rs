use anchor_lang::prelude::*;

declare_id!("9s91i9KwPPDJFDJirNqYuhCdxu2S7zq6ewdGqsHdrejB");

#[program]
pub mod my_project {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        msg!("Greetings from: {:?}", ctx.program_id);
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize {}
