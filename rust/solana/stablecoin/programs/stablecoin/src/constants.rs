use anchor_lang::prelude::*;
// 定义 config 的种子
pub const SEED_CONFIG_ACCOUNT:&[u8] = b"config";
// 定义 mint 的种子
pub const SEED_MINT_ACCOUNT:&[u8] = b"mint";

// 这个将是抵押账户的种子
pub const SEED_COLLATERAL_ACCOUNT:&[u8] = b"collateral";

// 这个将是存款人的稳定币账户的种子
pub const SEED_SOL_ACCOUNT:&[u8] = b"sol";

#[constant]
// sol to usd 的价格的id
pub const FEED_SOL_TO_USD_ID:&str = "0xef0d8b6fda2ceba41da15d4095d1da392a0d2f8ed0c6c7bc0f4cfac8c280b56d";
pub const MINT_DECIMALS:u8 = 9;
// 最大的超时时间
pub const MAXIMUM_AGE:u64 = 60; // 
// 定义价格计算的小数点,因为价格 返回的是10^8
// 但是我们需要的是10^10,所以我们需要调整小数点
pub const PRICE_FEED_DECIMALS_ADJUSTMENT:u128 = 10;


// 清算门槛，这意味着抵押率已超过200%
pub const LIQUIDATION_THRESHOLD:u64 = 50;

// 清算奖金，清算人将获得10%的奖励
pub const LIQUIDATION_BONUS:u64 = 10;

// 最低健康指数，低于1时,账户可以被清算
pub const MIN_HEALTH_FACTOR:u64 = 1;

