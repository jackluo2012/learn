use anchor_lang::prelude::*;
use anchor_lang::system_program::{transfer, Transfer};

declare_id!("A4UcmU4WQyPtdUPKUKtPcY8gQNiuRAdBNzs3K2Q7xuQY");

#[error_code]
pub enum ErrorCode {
    #[msg("Already initialized")]
    AlreadyInitialized,
}

#[program]
pub mod bank_one {
    use super::*;
    // 存款指令 ，存款 有金额
    pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
        if ctx.accounts.bank.initialized {
            return Err(ErrorCode::AlreadyInitialized.into());
        }
        // 拥有一家银行
        //  因为我们还没有创建它，所以它会设置所有必填的字段
        //  如果账户创建了怎么办
        *ctx.accounts.bank = Bank {
            // 权力
            authority: ctx.accounts.authority.key(),
            // 余额
            bank_balance: ctx.accounts.bank.bank_balance + amount,
            //  bump 随机数,只是为了像pda 一样
            bump: ctx.bumps.bank,
            initialized: true,
        };
        // 打印 银行信息
        msg!("{:#?}", ctx.accounts.bank);
        // 我们把钱存入银行
        transfer(
            CpiContext::new(
                ctx.accounts.system_program.to_account_info(),
                Transfer {
                    from: ctx.accounts.authority.to_account_info(),
                    to: ctx.accounts.bank.to_account_info(),
                },
            ),
            amount,
        )?;
        Ok(())
    }
// 取款指令
    pub fn withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
        // 减少银行余额
        ctx.accounts.bank.bank_balance -= amount;
        // 替换 lamports 转至你的账户
        ctx.accounts.bank.sub_lamports(amount)?;
        ctx.accounts.authority.add_lamports(amount)?;

        // 打印 银行信息
        msg!("{:#?}", ctx.accounts.bank);
        Ok(())
    }
}

// 账目，看看他们是否有正确
// 他们是否具有正确的签名权限
// 有不同的程序吗，
// 是否缺少所有权检查 

#[derive(Accounts)]
pub struct Deposit<'info> {
    #[account(mut)]
    // 签名者的权限
    pub authority: Signer<'info>,
    // 该银行的付款人是创建者或是权威机构
    #[account(
        init_if_needed,
        payer = authority,
        space = 8 + Bank::INIT_SPACE,
        seeds = [b"bank"],
        bump,
    )]
    pub bank: Account<'info, Bank>,
    // 还有一个系统 转账程序
    pub system_program: Program<'info, System>,
}
// 这是一个提款结构
#[derive(Accounts)]
pub struct Withdraw<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,
    // 可变的，只有一个权威的银行
    #[account(
        mut,
        // 确保只有权威机构才能提款
        has_one = authority,
        seeds = [b"bank"],
        bump,
    )]
    pub bank: Account<'info, Bank>,
}

// 银行的结构
#[account]
#[derive(InitSpace, Debug)]
pub struct Bank {
    pub authority: Pubkey,
    pub bank_balance: u64,
    pub bump: u8,
    // 检查这些简单的方法是,添加一些布尔值
    // 是否已经初始化了
    pub initialized: bool,
}