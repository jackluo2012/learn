use anchor_lang::prelude::*;

// 定义存储帐号的属性
// 定义一个solana的存储帐号,会占用存储空间
// 这个账号的创建者是谁
// 我们能初始化多个用户帐号，对于 使用此程序 的用户

#[account]
#[derive(InitSpace)]
pub struct User {
    pub owner: Pubkey, // 创建这个帐号的是谁
    // 我们需要知道 存入 或是代入 sol 的数量
    //如果要扩长，如何针对多种资产进行更新
    // 借贷协议不止两个,最好的资产管理 所有资产的存储
    // 只需明确说明结构中的每个资产
    pub deposited_sol: u64,
    pub deposited_sol_shares: u64,// 存入的sol的份额,股票
    pub borrowed_sol: u64,// 我们借了多少sol
    pub borrowed_sol_shares: u64, // 借入的sol的份额
    pub deposited_usdc: u64, // 存入的usdc的余额
    pub deposited_usdc_shares: u64, // 存入的usdc的份额
    pub borrowed_usdc: u64,// 我们借了多少usdc
    pub borrowed_usdc_shares: u64, // 借入的usdc的份额
    // 我们需要存入 USDC 的铸币地址，方便跟踪
    pub usdc_address: Pubkey,
    //帐户的最后更新时间
    pub last_updated: i64,
    // 已存入了或借入了多少 USDC.
    // 我们还要跟踪股票，我们将使用股票计算利息
    // 在指令中的逻辑
    // 用户最后的借款时间
    pub last_updated_borrowed: i64,

}

// 我们要跟踪另一个是银行，在供货协议上，我们想初如化银行，保留银行的状态 
// 每个银行都 有一个权利机构 
// 这个权力 是谁将，拥有特殊权限 ，更改银行配置
#[account]
#[derive(InitSpace)]
pub struct Bank {
    // 这个权力 是谁将，拥有特殊权限 ，更改银行配置
    pub authority: Pubkey,
    // 我们需要保存一个铸币地址,那将是资产的铸币地址
    pub mint_address: Pubkey,
    // 跟踪银行的总存款
    pub total_deposits: u64,
    // 然后是存款份额
    pub total_deposits_shares: u64,
    // 跟踪银行的总借款
    pub total_borrows: u64,
    // 然后是借款份额
    pub total_borrows_shares: u64,
    // 现在每个帐号都可以被 清算了
    // 我们想要追踪，清算门槛
    // 清算奖金，平仓，因子和最大LTV
    // 这些计算都需要常数 -》 根据资产变动数-> 我们存放在银行中
    // 帐户是否健康
    // 我们会把它存放 在资产银行中
    //清算阈值
    pub liquidation_threshold: u64,
    // 清算奖奖金
    pub liquidation_bonus: u64,
    // 平仓因子 -> 清算关闭因子是抵押的百分比，可以被 清算，有清算奖金 ，这是清算的百分比，
    // 将被 送往清算人
    // 什么为清算奖金
    // 有了清算门槛
    // 由于抵押不足，可以被清算
    pub liquidation_close_factor: u64,
    // 最大LTV ,是抵押品的最大百分比，可以为特定资产借入.
    pub max_ltv: u64,
    // 跟踪最后的时间
    pub last_updated: i64,
    // 存款利息
    pub interest_rate: u64,
}

