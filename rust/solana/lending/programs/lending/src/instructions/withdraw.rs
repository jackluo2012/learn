// 取款

use anchor_lang::{accounts::signer, prelude::*};
use anchor_spl::{
    associated_token::AssociatedToken, token, token_interface::{self, Mint, TokenAccount, TokenInterface, TransferChecked}
    
};
use std::f64::consts::E;
use crate::state::{Bank, User};
use crate::error::ErrorCode;
// 定义提款的结构

#[derive(Accounts)]
pub struct Withdraw<'info> {
    #[account(mut)]
    pub signer: Signer<'info>,
    // 我们需要一个铸币地址
    // 这将是我们提款的铸币地址
    pub mint: InterfaceAccount<'info, Mint>,
    // 我们需要一个银行帐户
    // 这将是我们提款的银行帐户
    #[account(
        mut,
        seeds = [mint.key().as_ref()],
        bump
    )]
    pub bank: Account<'info, Bank>,
    // 我们需要一个银行帐户
    // 这将是我们提款的银行帐户
    #[account(
        mut,
        seeds = [
            b"treasury".as_ref(),
            mint.key().as_ref()
        ],
        bump
    )]
    pub bank_token_account: InterfaceAccount<'info, TokenAccount>,
    // 我们需要一个用户帐户
    // 这将是我们提款的用户帐户,铸币账户
    #[account(
        mut,
        seeds = [
            signer.key().as_ref()
        ],
        bump
    )]
    pub user_account: Account<'info, User>,
    // 我们需要一个用户令牌账户
    // 这将是我们提款的用户令牌账户,撤回资产
    // 他们将资 金存入了借贷协议 ，我们无法保证用户拥有这个账户，
    //  不存在就创建
    #[account(
        init_if_needed,
        payer = signer,
        associated_token::mint = mint,
        associated_token::authority = signer,
        associated_token::token_program = token_program,
    )]
    pub user_token_account: InterfaceAccount<'info, TokenAccount>,
    // 我们需要一个系统程序帐户
    // 这将是我们提款的系统程序帐户
    pub system_program: Program<'info, System>,
    // 我们需要一个令牌程序帐户
    // 这将是我们提款的令牌程序帐户
    pub token_program: Interface<'info, TokenInterface>,
    // 我们需要一个令牌程序帐户
    // 这将是我们提款的关联令牌程序帐户
    pub associated_token_program: Program<'info, AssociatedToken>,
}

// 处理提款的函数
// 确保用户存入了足够的资金 -> 代币 即可 提取的数量
// 他们提取的数量不能超过，已经存入 的代币数量
pub fn process_withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
    // 获取用户帐户
    let user_account = &mut ctx.accounts.user_account;
    
    let deposited_value:u64;
    // 检查 用记是存入 的是 usdc 还是 sol
    if ctx.accounts.mint.key() == user_account.usdc_address {
        deposited_value = user_account.deposited_usdc;
    } else {
        deposited_value = user_account.deposited_sol;
    }
    // 我们要计算利息，当用户存入资金时进行记录
    let time_diff = user_account.last_updated - Clock::get()?.unix_timestamp;
    
    // 检查提款的数量是否大于存入的数量
    // 更新银行信息
    let bank = &mut ctx.accounts.bank;
    // 使用复利公式计算利息
    // 我们可以计算一股的当前价值
    bank.total_deposits = (bank.total_deposits as f64 * E.powf(bank.interest_rate as f64 * time_diff as f64 / 100.0)) as u64;
    // 我们可以计算一股的当前价值
    let value_per_share = bank.total_deposits as f64 / bank.total_deposits_shares as f64;
    //计算出每股的价值,将存入的价值, 按照每股的价值来计算
    let user_value =deposited_value as f64 /value_per_share;
    
    if user_value < amount as f64 {
        return Err(ErrorCode::InsufficientFunds.into());
    }
    
    
    
    // 执行cpi 转移
    let transfer_cpi_accounts = TransferChecked {
        // 银行转到个人
        from: ctx.accounts.bank_token_account.to_account_info(),
        to: ctx.accounts.user_token_account.to_account_info(),
        // 这个应该是bank的key
        authority: ctx.accounts.bank_token_account.to_account_info(),
        mint: ctx.accounts.mint.to_account_info(),
    };
    let transfer_cpi_program = ctx.accounts.token_program.to_account_info();
    let cpi_program = ctx.accounts.token_program.to_account_info();
    // 因为我们是从银行代币账户转账，因为它自己是PDA
    // 所以无论何时你想用pda 转账，
    // pda 必须签名 ，我们必须获取签名者的种子 
    // 我们先来定义 pda 的种子 是什么,对于银行代币账户 ，然后我们就可以转账了
    let mint_key = ctx.accounts.mint.key();
    let signer_seeds:&[&[&[u8]]] = &[&[
        b"treasury",
        mint_key.as_ref(),
        &[ctx.bumps.bank_token_account],
    ]];
    //  现在可以创建 cpi 上下文了
    let cpi_context = CpiContext::new_with_signer(
        transfer_cpi_program,
        transfer_cpi_accounts,
        signer_seeds,
    );
    //  我们还需要小数
    let decimals = ctx.accounts.mint.decimals;
    // 进行转移
    token_interface::transfer_checked(cpi_context, amount, decimals)?;
    
    //  以上用户可以将代币提取到自己的代币账户中
    // 更新银行信息
    let bank = &mut ctx.accounts.bank;
    // 更新银行的份额
    let shared_to_remove=(amount as f64 / bank.total_deposits as f64) * bank.total_deposits_shares as f64;
    // 更新用户的存款金额 
    // 更新用户存入 sol 或usdc 的金额

    if ctx.accounts.mint.key() == user_account.usdc_address {
        // 存款数和存款份额
        user_account.deposited_usdc = user_account.deposited_usdc.checked_sub(amount).unwrap();// .ok_or(ErrorCode::ArithmeticOverflow)?;
        user_account.deposited_usdc_shares = user_account.deposited_usdc_shares.checked_sub(shared_to_remove as u64).unwrap();// .ok_or(ErrorCode::ArithmeticOverflow)?;
    } else {
        // 针对 sol
        user_account.deposited_sol = user_account.deposited_sol.checked_sub(amount).unwrap();// .ok_or(ErrorCode::ArithmeticOverflow)?;
        user_account.deposited_sol_shares = user_account.deposited_sol_shares.checked_sub(shared_to_remove as u64).unwrap();// .ok_or(ErrorCode::ArithmeticOverflow)?;
    }
    // 更新银行信息
    bank.total_deposits = bank.total_deposits.checked_sub(amount).unwrap();
    bank.total_deposits_shares = bank.total_deposits_shares.checked_sub(shared_to_remove as u64).unwrap();// .ok_or(ErrorCode::ArithmeticOverflow)?;
    // 更新用户的最后更新时间
    user_account.last_updated = Clock::get()?.unix_timestamp;

    Ok(())
}