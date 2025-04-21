// 定义一个清算指令

use std::f64::consts::E;

use anchor_lang::prelude::*;
use anchor_spl::{
    associated_token::AssociatedToken, token, token_interface::
    {
        self,
        Mint, MintTo, 
        TokenAccount, 
        TokenInterface,
        TransferChecked,
    }
};
use pyth_solana_receiver_sdk::price_update::{ get_feed_id_from_hex, PriceUpdateV2};
use crate::{constants::{MAX_AGE, SOL_USD_FEED_ID, USDC_USD_FEED_ID}, state::{Bank, User},error::ErrorCode};

// 清算在什么时候 发生的呢？
// 按照协议偿还不良 账户的债务信息,作为 
// 回报，1.我们会收到抵押品，2.我们会收到清算奖励
//  清算金额的百分比， 他们收到的，激励清算人，并清算借贷协议 中不健康的账户
#[derive(Accounts)]
pub struct Liquidate<'info>{
    // 我们需要一个签名者，这个签名者是清算人
    #[account(mut)]
    pub liquidator: Signer<'info>,
//  我们需要了解资产的时时 价格
    pub price_update: Account<'info, PriceUpdateV2>,
    // 我们需要两个mint 账户
    // 我们需要抵押品的铸币账户 以及借款的铸币账户，我们需要进行两次转会
    // 因为一方是清盘人，正在偿还债务
    // 另一方是清算人接收抵押品
    // 这将是我们清算的铸币地址，抵押银行代币账户，借款银行，以及借来的银行代币账户
    pub collateral_mint: InterfaceAccount<'info, Mint>,
    // 借入的mint
    pub borrow_mint: InterfaceAccount<'info, Mint>,
    // 我们通过 银行对这些资产  抵押银行代币账户，借款银行，以及借来的银行代币账户
    // 这将有抵押铸币密钥 作为PDA
    #[account(
        mut,
        seeds = [
            collateral_mint.key().as_ref(),
        ],
        bump
    )]
    pub collateral_bank: Account<'info, Bank>,
    //借出银行
    #[account(
        mut,
        seeds = [
            borrow_mint.key().as_ref(),
        ],
        bump
    )]
    pub borrowed_bank: Account<'info, Bank>,
    // 我们需要每个人的帐账户,进行转换
    #[account(
        mut,
        seeds = [
            b"treasury".as_ref(),
            collateral_mint.key().as_ref()
        ],
        bump
    )]
    pub collateral_bank_token_account: InterfaceAccount<'info, TokenAccount>,
    // 我们需要每个人的帐账户,进行转换
    #[account(
        mut,
        seeds = [
            b"treasury".as_ref(),
            borrow_mint.key().as_ref()
        ],
        bump
    )]
    pub borrowed_bank_token_account: InterfaceAccount<'info, TokenAccount>,
    // 我们需要一个用户
    // 这将是我们清算的用户帐户
    #[account(
        mut,
        seeds = [
            liquidator.key().as_ref()
        ],
        bump
    )]
    pub user_account: Account<'info, User>,
    // 我们需要清算人的抵抵押品账户
    #[account(
        init_if_needed,
        payer = liquidator,
        associated_token::mint = collateral_mint,
        associated_token::authority = liquidator,
        associated_token::token_program = token_program,
    )]
    pub liquidator_collateral_token_account: InterfaceAccount<'info, TokenAccount>,
    // 以及借入的代币账户
    #[account(
        init_if_needed,
        payer = liquidator,
        associated_token::mint = borrow_mint,
        associated_token::authority = liquidator,
        associated_token::token_program = token_program,
    )]
    pub liquidator_borrowed_token_account: InterfaceAccount<'info, TokenAccount>,
    // 我们需要一个系统程序帐户
    pub system_program: Program<'info, System>,
    // 我们需要一个令牌程序帐户
    pub token_program: Interface<'info, TokenInterface>,
    // 我们需要一个令牌程序帐户
    pub associated_token_program: Program<'info, AssociatedToken>,
}
// 执行清算的函数
// 1. 我们需要获取清算的价格
pub fn process_liquidate(ctx: Context<Liquidate>, amount: u64) -> Result<()> {
    //加载抵押银行和用户
    // 以及价格更新 用户，因为我们想知道 有多少抵押品
    // 用户只需在协议上验证，他们的账户不健康，在处理清算前
    let collateral_bank = &mut ctx.accounts.collateral_bank;
    // 借出的银行
    let borrowed_bank = &mut ctx.accounts.borrowed_bank;
    let user  = &mut ctx.accounts.user_account;
    // 抵押吕和借入总额
    let price_update = &ctx.accounts.price_update;
    //  计算sol的价格
    let sol_feed_id = get_feed_id_from_hex(SOL_USD_FEED_ID)?;
    let usdc_feed_id = get_feed_id_from_hex(USDC_USD_FEED_ID)?;
    let sol_price = price_update.get_price_no_older_than(&Clock::get()?, MAX_AGE, &sol_feed_id)?;
    // 从pyth 上获取实际的USDC价格
    let usdc_price = price_update.get_price_no_older_than(&Clock::get()?, MAX_AGE, &usdc_feed_id)?;
    
    // 清算的总价值 
    let total_collateral:u64;
    // 用户的总借
    let total_brrowed:u64;
    // 获取清算的价格
    match ctx.accounts.collateral_mint.to_account_info().key() {
        // 如何抵押的是usdc
        key if key == user.usdc_address => {
            // 获取清算价格
            let new_usdc = calculate_accrued_interest(
                user.deposited_usdc, collateral_bank.interest_rate,
                user.last_updated)?;

            total_collateral = usdc_price.price as u64 * new_usdc;
            // 借出的sol
            let new_sol = calculate_accrued_interest(
                user.borrowed_sol, collateral_bank.interest_rate,
                user.last_updated_borrowed)?;
            total_brrowed = sol_price.price as u64 * new_sol;


        },
        _ => {
            // 如果抵押的是sol
            let new_sol = calculate_accrued_interest(
                user.deposited_sol, collateral_bank.interest_rate,
                user.last_updated)?;
            total_collateral = sol_price.price as u64 * new_sol;
            // 借出的usdc
            let new_usdc = calculate_accrued_interest(
                user.borrowed_usdc, 
                collateral_bank.interest_rate,
                user.last_updated_borrowed)?;            
            // 借出的usdc
            total_brrowed = usdc_price.price as u64 * new_usdc;
        }
    }
    //计算健康因子
    // 抵押品总额 乘以 清算的门槛 / 借入的总额
    // 如果健康因素低于一，那么该账户就是一健康的，可以被清算
    let health_factor = (total_collateral * collateral_bank.liquidation_threshold) / total_brrowed;
    if health_factor > 1 {
        return Err(ErrorCode::NotUnderCollateralized.into());
    }
    // 开始清算，第一步，成为清算人，向银行偿还借款
    // 所以我们要转账到银行
    let transfer_to_bank = TransferChecked{
        // 借入的代币账户
        from: ctx.accounts.liquidator_borrowed_token_account.to_account_info(),
        // 借入的银行的代币账户
        to: ctx.accounts.borrowed_bank_token_account.to_account_info(),
        authority: ctx.accounts.liquidator.to_account_info(),
        mint: ctx.accounts.borrow_mint.to_account_info(),
    };// 以上是借来的银行的代币账户，我们正在偿还借来的资产
    let cpi_program = ctx.accounts.token_program.to_account_info();
    let cpi_ctx = CpiContext::new(
        cpi_program.clone(),
        transfer_to_bank,
    );
    // 这是来自关联代币账户，所以不需要签名seeds
    // 我们不想清算所有的 全部借款，我们实际上在
    // 1.贷款协议中使用了一个关闭因子
    // 平仓因子是抵押吕的百分比，可以被清算
    // 所以我们要使用收盘因子进行清算,以下算出的是清算的金额
    let liquidation_amount = total_brrowed.checked_mul(borrowed_bank.liquidation_close_factor).unwrap();
    // 开始进行第一次清算转账
    token_interface::transfer_checked(cpi_ctx, liquidation_amount, ctx.accounts.borrow_mint.decimals)?;
    //清算的第二部分，是从抵押品，转移，向清盘人呈交帐目
    // 它将偿还清算人发来的所有款项，偿还借款，还将包括一个额外的，清算奖金金额
    let Liquidator_amount = (liquidation_amount * collateral_bank.liquidation_bonus)+ liquidation_amount;
    let transfer_to_liquidator = TransferChecked{
        // 抵押的代币账户
        from: ctx.accounts.collateral_bank_token_account.to_account_info(),
        // 清盘人的代币账户
        to: ctx.accounts.liquidator_collateral_token_account.to_account_info(),
        authority: ctx.accounts.collateral_bank_token_account.to_account_info(),
        mint: ctx.accounts.collateral_mint.to_account_info(),
    };
    // 因为我们目前是银行转帐，所以它是pad,我们需要签名种子 。
    let mint_key = ctx.accounts.collateral_mint.key();
    let seeds:&[&[&[u8]]] = &[&[
        b"treasury".as_ref(),
        mint_key.as_ref(),
        &[ctx.bumps.collateral_bank_token_account],
        ]];
    let cpi_ctx_to_liquidator = CpiContext::new_with_signer(
        cpi_program.clone(),
        transfer_to_liquidator,
        seeds,
    );
    // 开始转账
    token_interface::transfer_checked(cpi_ctx_to_liquidator, Liquidator_amount, ctx.accounts.collateral_mint.decimals)?;
    // 现在我们已经完成了清算，我们需要更新用户的帐户



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