use core::borrow;
use std::f64::consts::E;

use anchor_lang::prelude::*;
use anchor_spl::{
    associated_token::AssociatedToken, token, token_interface::{self, Mint, MintTo, TokenAccount, TokenInterface, TransferChecked}
};

use crate::state::{Bank, User};
use crate::error::ErrorCode;
#[derive(Accounts)]
pub struct Repay<'info> {
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
        ],
        bump
    )]
    pub bank_token_account: InterfaceAccount<'info, TokenAccount>,
    // 我们需要一个协议用户帐户（借款）
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
    //  我们现在需要用户想要借贷的 token (usdc,sol)
    #[account(
        mut,
        associated_token::mint = mint,
        associated_token::authority = signer,
        associated_token::token_program = token_program,
    )]
    pub user_token_account: InterfaceAccount<'info, TokenAccount>,
    // 我们还需要一个账户来时时更新 价格 -> 预言机
    // pub price_account: Account<'info, PriceUpdateV2>,

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
// 还款的本质逻辑 是将用户的存款转移到银行的借款中
// 偿还 他们借入的金额
pub fn process_repay(ctx: Context<Repay>, amount: u64) -> Result<()> {
    
    // 获取用户的信息
    let user_account = &mut ctx.accounts.user_account;
    // 查找用户借入的资产 是什么，还要计算利息
    // 偿还的借款比借出的多，因为要有利息
    // 定义存入的金额
    let borrow_value:u64;
    match ctx.accounts.mint.to_account_info().key() {
        key if key == user_account.usdc_address => {
            // 还款的资产是 usdc
            borrow_value = user_account.borrowed_usdc;
        },
        _ => {
            // 还款的资产是 sol
            borrow_value = user_account.borrowed_sol;
        }        
    }
    // 计算时间差，算出利息
    let time_diff = user_account.last_updated_borrowed - Clock::get()?.unix_timestamp;
    // 获取银行的信息
    let bank = &mut ctx.accounts.bank;
    bank.total_borrows -= (bank.total_borrows as f64 * E.powf(time_diff as f64 * bank.interest_rate as f64)) as u64;
    // 更新 银行的份额
    let value_per_share = bank.total_borrows as f64 / bank.total_borrows_shares as f64;

    let user_value = borrow_value as f64 / value_per_share as f64;

    if amount > user_value as u64 {
        // 如果用户输入的利息大于用户借入的利息
        // 那么我们返回一个错误
        return Err(ErrorCode::OverRepay.into());
    }
    // 让我们从用户的账户转移到银行的账户
    let transfer_cpi_accounts = TransferChecked {
        // 如果用户输入的利息小于用户借入的利息
        // 那么我们返回一个错误
        // 我们需要转移CPI账户
        from: ctx.accounts.user_token_account.to_account_info(),
        // 到银行的代币账户
        to: ctx.accounts.bank_token_account.to_account_info(),
        // 我们需要权限授权者的signer  因为签名者拥有用户的令牌账户
        authority: ctx.accounts.signer.to_account_info(),
        // mnit 账户
        mint: ctx.accounts.mint.to_account_info(),
    };
    let cpi_program = ctx.accounts.token_program.to_account_info();
    // 定义要使用的CPI程序
    // 由于我们要转移所有的代币，由于 我们转的是从用户的账户到银行的账户，所以不需要pda种子
    let cpi_ctx = CpiContext::new(cpi_program, transfer_cpi_accounts);
    token_interface::transfer_checked(
        cpi_ctx,
        amount,
        ctx.accounts.mint.decimals,
    )?;
    // 更新 银行的信息
    let borrow_rate = amount.checked_div(bank.total_borrows).unwrap();
    // 计算借款 用户份额
    let user_shares = bank
        .total_borrows_shares
        .checked_mul(borrow_rate).unwrap();
    // 银行的借款总额
    match ctx.accounts.mint.to_account_info().key() {
        // 用户想要借入的是usdc
        key if key == user_account.usdc_address => {
            // 用户的sol的份额
            user_account.borrowed_usdc = user_account.borrowed_usdc.checked_sub(amount).unwrap();// .ok_or(ErrorCode::ArithmeticOverflow)?;
            // 用户的sol的余额
            user_account.borrowed_usdc_shares = user_account.borrowed_usdc_shares.checked_sub(user_shares).unwrap();// .ok_or(ErrorCode::ArithmeticOverflow)?;
        },
        _ => {            
            // 用户的sol的份额
            user_account.borrowed_sol = user_account.borrowed_sol.checked_sub(amount).unwrap();// .ok_or(ErrorCode::ArithmeticOverflow)?;
            // 用户的sol的余额
            user_account.borrowed_sol_shares = user_account.borrowed_sol_shares.checked_sub(user_shares).unwrap();// .ok_or(ErrorCode::ArithmeticOverflow)?;
        },        
    }
    // 更新 银行的信息
    // 银行的借款总额
    bank.total_borrows = bank.total_borrows.checked_sub(amount).unwrap();
    // 银行的借款总额的份额
    bank.total_borrows_shares = bank.total_borrows_shares.checked_sub(user_shares).unwrap();

    Ok(())
}