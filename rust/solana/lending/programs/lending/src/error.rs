
use anchor_lang::prelude::*;

#[error_code]
pub enum ErrorCode {
     
    #[msg("余额不足")]
    InsufficientFunds, // 余额不足
    // 这个错误是因为我们没有足够的余额来支付交易费用
    #[msg("请求超过了可借的金额")]
    OverBorrowableAmount, // 余额不足
    #[msg("请求超过了可还的金额")]
    OverRepay, // 股票不足
    // 这个错误是因为我们没有足够的余额来支付交易费用
    #[msg("用户没有抵押品，不能进行清算")]
    NotUnderCollateralized, // 银行无效
    // 这个错误是因为我们没有足够的余额来支付交易费用
    InvalidUser, // 用户无效
    // 这个错误是因为我们没有足够的余额来支付交易费用
}
