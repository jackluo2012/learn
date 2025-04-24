/// 持有所有状态的账户
use anchor_lang::prelude::*;

/// 定义抵押器账户结构
#[account]
#[derive(InitSpace,Debug)]
pub struct Collateral {
    // 跟踪存款人是谁
    pub depositor: Pubkey,
    // 跟踪存款人的,存入的sol的账户,这将是一个pda账户
    pub sol_account: Pubkey,
    // 跟踪存款人的,存入的稳定币的账户,设置为关联的令牌账户
    pub token_account: Pubkey,
    // 我们还要计算整个过程的健康因素 
    // 我们得计算每个账户的余额
    pub lamport_balance: u64,
    // 我们还将跟踪 铸造的代币数量
    pub amount_minted: u64,
    // 我们会保存bumps ,我们会把这笔钱存入抵押账户 
    // 以以Sol 账户的增长
    pub bump: u8,
    pub bump_sol_account: u8,
    // 这个账户是否初始化
    pub is_initialized: bool,
}
// 配置账户
//  我们要跟踪的是我们的配置账户
//  我们将保存所有的全球信息，整体稳定币的健康因素
#[account]
#[derive(InitSpace,Debug)]
pub struct Config {
    // 这将是一个权力账户，对于这个stablecoin 来说
    // 这个权威的钱包地址
    pub authority: Pubkey,
    // 这个稳定币的铸币账户
    pub mint_account: Pubkey,
    // 我们将面临，全球性的清算因素
    // 这将适用于每个抵押账户，了解它是否健康，是否需要清算
    // 清算门槛，清算阈值
    pub liquidation_threshold: u64,
    // 清算奖金，用于给清算人的奖励
    pub liquidation_bonus: u64,
    // 最低健康因素，如果低于这个值 账户可以被清算
    pub min_health_factor: u64,
    // 我们要保存bump配置账户的提升，以及稳定币的铸造账户PDA
    pub bump: u8,
    pub bump_mint_account: u8,
}
