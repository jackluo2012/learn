use anchor_lang::prelude::*;


//获取 pyth 实时的价格地址
// https://www.pyth.network/developers/price-feed-ids
#[constant]
//  SOL 对比 USD 的价格
pub const SOL_USD_FEED_ID: &str = "0xef0d8b6fda2ceba41da15d4095d1da392a0d2f8ed0c6c7bc0f4cfac8c280b56d"; 
//  USDC 对比 USD 的价格
pub const USDC_USD_FEED_ID: &str = "0xeaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a";

pub const MAX_AGE: u64 = 100; // 价格的最新时间戳,不能超过100秒