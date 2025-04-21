use core::borrow;
use std::f64::consts::E;

// 用户进行借款
use anchor_lang::prelude::*;
use anchor_spl::{
    associated_token::AssociatedToken, 
    token_interface::
    {
        self,
        Mint, MintTo, 
        TokenAccount, 
        TokenInterface,
        TransferChecked,
    }
};
use pyth_solana_receiver_sdk::price_update::{ get_feed_id_from_hex, PriceUpdateV2};
use crate::{constants::{MAX_AGE, SOL_USD_FEED_ID, USDC_USD_FEED_ID}, state::{Bank, User}};
use crate::error::ErrorCode;

#[derive(Accounts)]
pub struct Borrow<'info> {
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
            // mint.key().as_ref()
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
        init_if_needed,
        payer = signer,
        associated_token::mint = mint,
        associated_token::authority = signer,
        associated_token::token_program = token_program,
    )]
    pub user_token_account: InterfaceAccount<'info, TokenAccount>,
    // 我们还需要一个账户来时时更新 价格 -> 预言机
    pub price_account: Account<'info, PriceUpdateV2>,
    
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
// 为了能够借钱，我们借的是另一种 资 产,比我们作为 抵押品存入的资产更有价值，
// 我们要了解我们拥有的资产价值
// 作为美元抵押品，以便进行比较，我们需要使用pyth oracle 来获取价格
// 获取时时的价格


//处理用户借款的逻辑 > 用户指定借款的金额
pub fn process_borrow(ctx: Context<Borrow>, amount: u64) -> Result<()> {
    //  我们应该如何处理通过处理协议上的借贷
    //  用户在银行存入了多少抵押品
    //  我们必须抵押多少才能借款
    // 所以你将拥有几项资产，必须作为抵押品来计算，此协议我们只有USDC 和SOL
    // 我们还有存款，金额的利息，用户有好多抵押品。
    // 加载银行和用户账户
    let bank = &mut ctx.accounts.bank;
    let user_account = &mut ctx.accounts.user_account;
    // 获取抵押品的真实价值，加载价格更新账户
    let price_update = &mut ctx.accounts.price_account;
    // 获取抵押品
    let total_collateral:u64;
    // 获取用户使用什么作为抵押品
    match ctx.accounts.mint.to_account_info().key() {
        // 用户想要借入的是usdc
        key if key == user_account.usdc_address => {
            // 所以要获取 用户存入的 SOl 的真实价格
            let sol_feed_id = get_feed_id_from_hex(SOL_USD_FEED_ID)?;
            // 从pyth 上获取实际的SOL价格
            let sol_price = price_update.get_price_no_older_than(&Clock::get()?, MAX_AGE, &sol_feed_id)?;
            // 我们有了sol的价格,所以我们要计算利息
            let new_value = calculate_accrued_interest(user_account.deposited_sol, bank.interest_rate, user_account.last_updated)?;
            //  有多少sol 乘以 sol的价格 + 利息
            total_collateral = sol_price.price as u64 * new_value;
        },
       
        _ => {
            // 用户想要借入的是usdc
            // 所以要获取 用户存入的 USDC 的真实价格
            let usdc_feed_id = get_feed_id_from_hex(USDC_USD_FEED_ID)?;
            // 从pyth 上获取实际的USDC价格
            let usdc_price = price_update.get_price_no_older_than(&Clock::get()?, MAX_AGE, &usdc_feed_id)?;
            // 我们有了usdc 的价格,所以我们要计算利息
            let new_value = calculate_accrued_interest(user_account.deposited_usdc, bank.interest_rate, user_account.last_updated)?;
            //  有多少sol 乘以 sol的价格 + 利息
            total_collateral = usdc_price.price as u64 * new_value;
        },
    }
    // 总抵押品的价值 必须 小于，或者等于总抵押品，乘以资产的清算门槛
    // 我们得算出导致他们的帐户不健康

    let borrowable_amount = total_collateral.checked_mul(bank.liquidation_threshold).unwrap();
    // 我们要检查 用户是否要以借款,他们是否要求金额 
    if borrowable_amount < amount {
        return Err(ErrorCode::OverBorrowableAmount.into());
    }
    // 我们已经考虑过用户的抵押品了和利息了
    // 所以我们开始处理借款 我们需要cpi account
    let transfer_cpi_accounts = TransferChecked {
        from: ctx.accounts.bank_token_account.to_account_info(),
        to: ctx.accounts.user_token_account.to_account_info(),
        authority: ctx.accounts.bank_token_account.to_account_info(),
        mint: ctx.accounts.mint.to_account_info(),
    };
    // 我们需要一个cpi上下文
    let cpi_program = ctx.accounts.token_program.to_account_info();
    // 我们要部署上下文签名,来自己银行的账户 即 PDA,所以我们必须定义签名的种子 ,供CPI处理
    let mint_key = ctx.accounts.mint.key();
    let seeds:&[&[&[u8]]] = &[
        &[
            b"treasury".as_ref(),
            mint_key.as_ref(),
            &[ctx.bumps.bank_token_account],
        ]
    ];
    let cpi_ctx = CpiContext::new_with_signer(cpi_program, transfer_cpi_accounts, seeds);
    
    token_interface::transfer_checked(cpi_ctx, amount, ctx.accounts.mint.decimals)?;
    // 转帐已完成，我们更新 用户帐户银行信息
    // 我们得考虑总借款额是否为零
    if bank.total_borrows == 0 {
        // 如果没有借款，我们更新银行信息
        bank.total_borrows = amount;
        bank.total_borrows_shares = amount;
    }     
    // 我们根据借款的比率，计算用户的份额，与存款份额相同
    
    // 计算借款比率
    let borrow_rate = amount.checked_div(bank.total_borrows).unwrap();
    let user_shares = bank.total_borrows_shares.checked_mul(borrow_rate).unwrap();

    // 用于代入或借出sol或usdc的份额
    match ctx.accounts.mint.to_account_info().key() {
        // 用户想要借入的是usdc
        key if key == user_account.usdc_address => {
            // 用户的sol的份额
            user_account.borrowed_usdc = amount;
            // 用户的sol的余额
            user_account.borrowed_usdc_shares = user_shares;
        },
       
       _ => {            
            // 用户的sol的份额
            user_account.borrowed_sol = amount;
            // 用户的sol的余额
            user_account.borrowed_sol_shares = user_shares;
        },
       
    }
    // 更新 银行的信息
    // 银行的借款总额
    bank.total_borrows += amount;
    // 银行的借款份额
    bank.total_borrows_shares += user_shares;

    // 更新用户的最后更新时间
    user_account.last_updated_borrowed = Clock::get()?.unix_timestamp;




    Ok(())
}

// 我们有了sol的价格,所以我们要计算利息
pub fn calculate_accrued_interest(
    deposited: u64,
    interest_rate: u64,
    last_updated: i64,
) -> Result<u64> {
    //获取时间戳
    // 也就是存取的价值，乘以E的利率次方
    let current_time = Clock::get()?.unix_timestamp ;
    // 计算时差
    let time_diff = current_time - last_updated;
    // 计算利息 这个是利息的公式
    let new_value = (deposited as f64 * E.powf(interest_rate as f64 * time_diff as f64) as f64) as u64;
    
    Ok(new_value)
}