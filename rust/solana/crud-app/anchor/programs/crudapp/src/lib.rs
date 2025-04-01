#![allow(clippy::result_large_err)]

use anchor_lang::prelude::*;

declare_id!("DwM4sXKyV3eZphys9G1TMAXe1agKHpBhcTD3MZcBMPcv");

#[program]
pub mod crudapp {
    use super::*;
    
    // 创建一个journal entry
    pub fn create_journal_entry(
        ctx: Context<CreateJournalEntry>,
        title: String,
        message: String,
    ) -> Result<()> {
        let journal_entry_state = &mut ctx.accounts.journal_entry;
        journal_entry_state.owner = ctx.accounts.owner.key();
        journal_entry_state.title = title;
        journal_entry_state.message = message;
       Ok(())
    }
    // 更新一个journal entry
    pub fn update_journal_entry(
        ctx: Context<UpdateJournalEntry>,
        title: String,
        message: String,
    ) -> Result<()> {
        let journal_entry_state = &mut ctx.accounts.journal_entry;
        journal_entry_state.title = title;
        journal_entry_state.message = message;
        Ok(())
    }

    // 删除一个journal entry
    pub fn delete_journal_entry(
        ctx: Context<DeleteJournalEntry>,
        title: String,
    ) -> Result<()> {
        let journal_entry_state = &mut ctx.accounts.journal_entry;
        // journal_entry_state.close(ctx.accounts.owner)?;
        Ok(())
    }
  }

#[derive(Accounts)]
#[instruction(title: String)] // 设置title 来自用户输入 
pub struct CreateJournalEntry<'info> {
    #[account(init, 
      payer = owner, 
      seeds = [title.as_bytes(), owner.key().as_ref()],
      bump,
      space = 8 + JournalEntryState::INIT_SPACE)
    ]
    pub journal_entry: Account<'info, JournalEntryState>,
    #[account(mut)]
    pub owner: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(title: String)] // 设置title 来自用户输入 
pub struct UpdateJournalEntry<'info> {
    #[account(mut, 
      seeds = [title.as_bytes(), owner.key().as_ref()],
      bump,
      realloc = 8 + JournalEntryState::INIT_SPACE,// 重新分配空间
      realloc::payer = owner,
      realloc::zero = true,
    )]
    pub journal_entry: Account<'info, JournalEntryState>,
    #[account(mut)]
    pub owner: Signer<'info>,
    pub system_program: Program<'info, System>,

}
#[derive(Accounts)]
#[instruction(title: String)]
pub struct DeleteJournalEntry<'info> {
    #[account(mut, 
      seeds = [title.as_bytes(), owner.key().as_ref()],
      bump,
      close = owner,
    )]
    pub journal_entry: Account<'info, JournalEntryState>,
    #[account(mut)]
    pub owner: Signer<'info>,
    pub system_program: Program<'info,System>,
    pub rent: Sysvar<'info, Rent>,
}
#[account]
#[derive(InitSpace)]
pub struct JournalEntryState {
  pub owner: Pubkey,
  #[max_len(50)]
  pub title: String,
  #[max_len(1000)]
  pub message: String,
}
