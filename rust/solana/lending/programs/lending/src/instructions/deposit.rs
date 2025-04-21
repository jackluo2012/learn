// deposit
/// 写存款指令
/// 我们需要考虑需要的所有账户
/// 以便用户能够向协议中存款
/// 我们首先要考虑的是签名者
/// 这将是指令的签署人,存款指示
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

use crate::state::{Bank, User};

// 存储结构
#[derive(Accounts)]
pub struct Deposit<'info>{
    #[account(mut)]
    pub signer:Signer<'info>,
    //我们需要的是铸币币账户
    // 用于我们深度存入的令牌
    pub mint:InterfaceAccount<'info,Mint>,
    // 我们现在需要银行帐记，就是和银行相关的信息
    // 我们要更新银行的信息
    // 当把代币存入银行时,该令牌将被发送到银行令牌账户,所以我们需要银行账户
    #[account(
        mut,
        seeds = [mint.key().as_ref()],
        bump
    )]
    pub bank:Account<'info,Bank>,
    // 向银行存款
    #[account(
        mut,
        // 种子 设置为金库和铸币厂钥匙
        seeds = [
            b"treasury".as_ref(),
            mint.key().as_ref()
        ],
        bump
    )]
    pub bank_token_account:InterfaceAccount<'info,TokenAccount>,
    // 我们需要一个用户账户
    // 存储，所有令牌的地方 ,对于使用借贷协议 的特定用户
    #[account(
        mut,
        seeds = [
            signer.key().as_ref()
        ],
        bump
    )]
    pub user_account:Account<'info,User>,
    // 我们有了银行，且也
    // 有了银行保管 代币的帐户
    // 有用户，以及用户状态 
    // 我们需要一个用户令牌账户。这将接收我们的存入的代币，并将其转入银行代币账户中。
    // 所以我们需要一个关联代币账户,以及代币铸造地址
    // 我们将它存入 银行
    #[account(
        associated_token::mint = mint,
        associated_token::authority = signer,
        associated_token::token_program = token_program,
    )]
    pub user_token_account: InterfaceAccount<'info,TokenAccount>,
    pub token_program: Interface<'info,TokenInterface>,
    pub system_program: Program<'info, System>,
    pub assoc_token_program: Program<'info, AssociatedToken>,
    pub rent: Sysvar<'info, Rent>,
}

// 我们如何 将代币 存入银行
//  我们想要进行 CPI 转移 ，从用户的代币帐户转入 银行的代币帐户
// 然后我们要计算新增股份，向银行发行新股，向用户发行新股
// 我们需要更新用户的存款金额，以及抵押品的总价值
// 然后再更新 银行状态
// 从用户的代币账户 存入银行
// amount 存款的数量
pub fn process_deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
    
    // 我们需要转移CPI账户
    let transfer_cpi_accounts = TransferChecked {
        // 如果你正在转移代币，来自用户的代币账户
        from: ctx.accounts.user_token_account.to_account_info(),
        // 到银行的代币账户
        to: ctx.accounts.bank_token_account.to_account_info(),
        // 我们需要权限授权者的signer  因为签名者拥有用户的令牌账户
        authority: ctx.accounts.signer.to_account_info(),
        // mnit 账户
        mint: ctx.accounts.mint.to_account_info(),       
    };
    // 定义要使用的CPI程序
    // 由于我们要转移所有的代币，将是一个接口账户代币
    //  我们可以使用令牌程序 
    let cpi_program = ctx.accounts.token_program.to_account_info();
    // 通过消费者价格指数计划,以及转移CPI账户
    let cpi_ctx = CpiContext::new(cpi_program, transfer_cpi_accounts);
    // 我们需要decimals
    let decimals = ctx.accounts.mint.decimals;
    //执行转帐 从用户的账户到银行账户
    token_interface::transfer_checked(cpi_ctx, amount ,decimals)?;
    // 更新银行信息，用户账户信息,以反映这种 转移
    // 先转换银行信息
    let bank = &mut ctx.accounts.bank;
    
    // 如果 银行的总额是0 
    if bank.total_deposits == 0 {
        bank.total_deposits = amount;
        bank.total_deposits_shares = amount;
    } 
    // 为了能计算份额，我们想在银行状态中更新 
    // 我们除法和乘法，考虑溢出,和下溢错误，用RUST中的除法和乘法,能够处理发生的任何错误
    // 如果发生错误，我们将返一个值 ，或none
    // 如果 是除会发生错误会 恐慌
    // 所以我们要设定存款比率，就是我们计算，用户份额所需要的份额
    // 这将是存款股份，是总存款股价乘 以存款 比率。
    // 我们先要计算存款比率，即存款金额 除于，银行存款总额
    // 我们存入 的金额 除于 银行存款总额
    let deposit_ratio = amount
        .checked_div(bank.total_deposits).unwrap();// .ok_or(ErrorCode::ArithmeticOverflow)?;
    // 计算存款 用户份额
    let user_shares = bank
            .total_deposits_shares
            .checked_mul(deposit_ratio).unwrap();// .ok_or(ErrorCode::ArithmeticOverflow)?;
        
    // 我们还想加载用户帐户，更新用户的信息
    // 所以我们就是需要获取usdc地址的地方
    // 我们保存了用户状态 
    // 我们要做的就是有一个匹配声明
    let user = &mut ctx.accounts.user_account;
    // 卫语句下面是个
    match ctx.accounts.mint.to_account_info().key() {
        // 如果密钥等于用户的usdc地址
        // 我们要更新用户,存入 usdc的金额
        key if key == user.usdc_address => {
            // 更新用户的usdc存款金额
            user.deposited_usdc = user.deposited_usdc.checked_add(amount).unwrap();// .ok_or(ErrorCode::ArithmeticOverflow)?;
            // 更新用户的usdc存款股份
            user.deposited_usdc_shares = user.deposited_usdc_shares.checked_add(user_shares).unwrap();// .ok_or(ErrorCode::ArithmeticOverflow)?;
        },
        // 它只是一个双资产协议，所以我只更新用户的sol存款金额
        _ => {
            // 更新用户的sol存款金额
            user.deposited_sol = user.deposited_sol.checked_add(amount).unwrap();// .ok_or(ErrorCode::ArithmeticOverflow)?;
            // 更新用户的sol存款股份
            user.deposited_sol_shares = user.deposited_sol_shares.checked_add(user_shares).unwrap();// .ok_or(ErrorCode::ArithmeticOverflow)?;
        }
    }
    // 让我们来考虑一个 借贷协议，有两种选择，
    // 当存入存款时，铸造一个抵押代币，创建一个股份
    // 我们希望更新用户的存款金额，存款股份，存款余额，存款余额
    // 我们要考虑存款余额，存款股份，借入金额，借入股份
    //  在整个协议中销毁和铸造代币

    // 计算银行的总额 
    bank.total_deposits = bank.total_deposits.checked_add(amount).unwrap();// .ok_or(ErrorCode::ArithmeticOverflow)?;
    // 更新银行的存款股份
    bank.total_deposits_shares = bank.total_deposits_shares.checked_add(user_shares).unwrap();// .ok_or(ErrorCode::ArithmeticOverflow)?;

    // 更新用户的存储时间
    // 这将是我们存入的时间
    user.last_updated = Clock::get()?.unix_timestamp;

    Ok(())
}