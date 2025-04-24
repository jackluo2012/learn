use anchor_lang::prelude::*;

#[error_code]
pub enum CustomError {
    #[msg("无效的价格")]
    InvalidPriceFeed, 
    #[msg("健康因素太低")]    
    BelowMinHealthFactor,
    #[msg("不能清理健康账户")]
    AboveMinHealthFactor,
}