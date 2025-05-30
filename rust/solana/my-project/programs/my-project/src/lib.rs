use anchor_lang::prelude::*;

declare_id!("6yGs7L1cYVdpJ6aLctSuLGE3CCX2K2RKomN35cdtp5ty");

#[program]
pub mod my_project {
    use super::*;
    use anchor_lang::system_program;
    // use std::collections::{HashMap,BTreeMap};
    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        msg!("Greetings from: {:?}", ctx.program_id);
        // 获取一个可变引用，允许更新账户数据
        let my_account = &mut ctx.accounts.my_account;
        my_account.data.push(42);
        my_account.data.push(7);
        msg!("data is {:?}",my_account.data);
        Ok(())
    }
    // 转帐程序
    pub fn transfer_sol_with_cpi(ctx: Context<TransferSolWithCpi>, amount: u64) -> Result<()> {
        let cpi_accounts = anchor_lang::system_program::Transfer {
            from: ctx.accounts.payer.to_account_info(),
            to: ctx.accounts.recipient.to_account_info(),
        };
        let cpi_program = ctx.accounts.system_program.to_account_info();

        anchor_lang::system_program::transfer(
            CpiContext::new(cpi_program, cpi_accounts),
            amount,
        )?;

        Ok(())
    }

}
// 自动生成账户验证逻辑
#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(init, payer = user, space = 8 + 1024)]
    pub my_account: Account<'info, MyAccount>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

// #标记和初始化账户数据结构
#[account]
pub struct MyAccount {
    pub data: Vec<u8>,//存储动态数组的数据字段
}
// TransferSolWithCpi上下文
#[derive(Accounts)]
pub struct TransferSolWithCpi<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,
    #[account(mut)]
    pub recipient: SystemAccount<'info>,
    pub system_program: Program<'info, System>,
}