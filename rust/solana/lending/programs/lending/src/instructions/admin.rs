/// 负责管理 整个借贷协议
use anchor_lang::prelude::*;
use anchor_spl::token_interface::{Mint, TokenAccount, TokenInterface};
use crate::state::{Bank,User};

// 初化一个银行
#[derive(Accounts)]
pub struct InitBank<'info> {
    #[account(mut)]
    // 这是一个发布者的签名
    pub signer: Signer<'info>,
    // 我们需要一种 Wrapped Sol 将成为SPL 代币的
    // 我们不需要处理任何与lampports相关的事情
    //以及系统帐户，我们要确保 所有铸币账户，将成为
    // 这些银行的接口账户
    // 铸币将来自己，代币接口
    pub mint: InterfaceAccount<'info, Mint>,
    // 初始化银行 
    #[account(
        init,
        payer = signer,
        space = 8 + Bank::INIT_SPACE,// 链上空间
        // 我们要将bank 变成一个pda ,所以要定义种子
        // 每家银行都有一个独特的铸币钥匙
        seeds = [mint.key().as_ref()],
        bump
    )]
    // 我们有银行，银行掌握着信息,到帐号
    pub bank: Account<'info, Bank>,
    // 我们还需要一个代币账户，为银行保管代币
    // 初始化一个代币账户，对银行来说
    #[account(
        init, 
        //付款人
        payer = signer, 
        token::mint = mint, 
        // 权限设置于我们自己
        token::authority = bank_token_account,
        // 我们不想使用关联的代币账户
        // 我们只想拥有一个带有PAD的令牌账户,
        // 所以这个账号是特定的, 到借贷协议银行
        seeds = [
            b"treasury".as_ref(),            
            mint.key().as_ref()
        ],
        bump
        )]
    pub bank_token_account: InterfaceAccount<'info,TokenAccount>,
    //还需要两个账号
    // 因为我们需要创建新的代币账户
    pub token_program: Interface<'info,TokenInterface>,

    // 我们初始化一个帐号，所以需要传递系统程序
    pub system_program: Program<'info, System>,
}


// 初始化银行
// 清算阈值
pub fn process_init_bank(ctx: Context<InitBank>, liquidation_threshold: u64,max_ltv:u64) -> Result<()> {
    // 保存需要的信息
    // 到银行的账户状态 
    let bank = &mut ctx.accounts.bank;
    // 更新 铸币地址
    bank.mint_address = ctx.accounts.mint.key();
    // 获取签名者
    bank.authority = ctx.accounts.signer.key();
    // 设置清算门槛
    bank.liquidation_threshold = liquidation_threshold;
    // 抵押的最大百分比，可以借入
    bank.max_ltv = max_ltv;
    // 设置成固定的5%
    bank.interest_rate = 0.05 as u64;
    Ok(())
}
//  我们还需要创建一个账户
// 这是一个用户账户
#[derive(Accounts)]
pub struct InitUser<'info> {
    #[account(mut)]
    pub signer: Signer<'info>,
    // 通过用户账户创建它,所以帐号需要初始化
    #[account(
        init,
        payer = signer,
        space = 8 + User::INIT_SPACE,
        seeds = [signer.key().as_ref()],
        bump
    )]
    pub user_account: Account<'info, User>,
    // 我们需要一个系统账户
    pub system_program: Program<'info, System>,
}

// 创建初始化指令
// 还需要一个usdc地址，只是我们要做检查 
// 在整个程序 中，我们只想追踪那个是什么.
//  如果优化这是个挑战 
// 如何跟踪和检查 您正在使用的minit 地址
pub fn process_init_user(ctx: Context<InitUser>,usdc_address:Pubkey) -> Result<()> {
    // 获取用户
    let user_account = &mut ctx.accounts.user_account;
    // 设置所有者
    user_account.owner = ctx.accounts.signer.key();
    user_account.usdc_address = usdc_address;
    
    Ok(())
}