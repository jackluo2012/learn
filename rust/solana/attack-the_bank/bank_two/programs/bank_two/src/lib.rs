use anchor_lang::prelude::*;
use anchor_lang::system_program::{transfer, Transfer};

declare_id!("312H8CZByRpD1cp4WcZS7pUVAs245NHGp1uNCyP1H3cL");

#[program]
pub mod bank_two {
    use super::*;

    pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
        let bank_account = &mut ctx.accounts.bank;
        bank_account.bank_balance += amount;

        if !bank_account.is_initialized {
            bank_account.is_initialized = true;
            bank_account.authority = ctx.accounts.authority.key();
            bank_account.bump = ctx.bumps.bank;
        }
        msg!("{:#?}", bank_account);

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

    pub fn withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
        ctx.accounts.bank.bank_balance -= amount;
        ctx.accounts.bank.sub_lamports(amount)?;
        ctx.accounts.authority.add_lamports(amount)?;
        msg!("{:#?}", ctx.accounts.bank);
        Ok(())
    }

    pub fn update_authority(ctx: Context<UpdateAuthority>) -> Result<()> {
        // 谁签署方了这笔交易
        // 1. 签名者必须是bank的authority
        // 2. bank的authority必须是ba
        
        ctx.accounts.bank.authority = ctx.accounts.new_authority.key();
        msg!("{:#?}", ctx.accounts.bank);
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Deposit<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,
    #[account(
        init_if_needed,
        payer = authority,
        space = 8 + Bank::INIT_SPACE,
        seeds = [b"bank"],
        bump,
    )]
    pub bank: Account<'info, Bank>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Withdraw<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,
    #[account(
        mut,
        // 检查整个权限的账户约束
        has_one = authority,
        seeds = [b"bank"],
        bump,
    )]
    pub bank: Account<'info, Bank>,
}

#[derive(Accounts)]
pub struct UpdateAuthority<'info> {
    
    // 如果是一个系统账户，那么它必须是一个签名者
    // 它不是一个singer,内部使用 has_one 约束
    pub authority: SystemAccount<'info>,
    // pub authority: Signer<'info>,
    pub new_authority: SystemAccount<'info>,
    #[account(
        mut,
        has_one = authority,
        seeds = [b"bank"],
        bump,
    )]
    pub bank: Account<'info, Bank>,
}

#[account]
#[derive(InitSpace, Debug)]
pub struct Bank {
    pub authority: Pubkey,
    pub bank_balance: u64,
    pub is_initialized: bool,
    pub bump: u8,
}