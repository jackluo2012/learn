// 处理报价
// 实际报价
use anchor_lang::prelude::*;
// 详细的报价信息
#[account]
#[derive(InitSpace)]
pub struct Offer {
    pub id :u64, // 谁
    pub maker: Pubkey, // 谁提供的报价
    pub token_mint_a: Pubkey, // 代币的mint地址
    pub token_mint_b: Pubkey, // 代币的mint地址
    pub token_b_wanted_amount: u64, // 代币的数量
    pub bump: u8, // 代币的数量    
}