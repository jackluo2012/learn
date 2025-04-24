use anchor_lang::{prelude::*, solana_program::native_token::LAMPORTS_PER_SOL};
use pyth_solana_receiver_sdk::price_update::{get_feed_id_from_hex, PriceUpdateV2};

use crate::{ 
    constants::PRICE_FEED_DECIMALS_ADJUSTMENT, Collateral, Config, CustomError, FEED_SOL_TO_USD_ID, MAXIMUM_AGE
};
// 检查健康状态

pub fn check_health_factor(
    // 获取抵押品
    collateral: &Account<Collateral>,
    // 获取配置账户
    config: &Account<Config>,
    // 获取价格更新
    price_feed: &Account<PriceUpdateV2>,
) -> Result<()> {
    let health_factor = calculate_health_factor(
        collateral,
        config,
        price_feed,
    )?;
    // 健康因子 的最低因素
    require!(health_factor >= config.min_health_factor, CustomError::BelowMinHealthFactor);
    Ok(())
}


//  已铸造了多少币代币，sol 存款，sol 存款是否足够
// 配置账户,才能获得全局信息,其中包括清算门槛,以及最低健康因素
// 我们还需要来自 PYTH 的价格更新
//  能够获取每项资产的实时 价格数据 

pub fn calculate_health_factor(
    // 获取抵押品
    collateral: &Account<Collateral>,
    // 获取配置账户
    config: &Account<Config>,
    // 获取价格更新
    price_feed: &Account<PriceUpdateV2>,
) -> Result<u64> {
    
    // 获取存入的抵押品也就是 sol的美元价值 ,为清算门槛
    let collateral_value_in_usd = get_usd_value(&collateral.lamport_balance,price_feed)?;
    // 调整 清算门槛 也是抵押品的价值
    let collateral_adjuested_for_liquidation_threshold = collateral_value_in_usd * config.liquidation_threshold / 100;
    // 我们要考虑健康因子,调整抵押品,清算门槛除以铸造数量
    //  如果 有人拥有一个账户,铸造量为0
    if collateral.amount_minted == 0 {
        msg!("Health Factor is MAX");
        return Ok(u64::MAX);
    }
    // 如果 不为0 ,我们将通过 降法来计算健康因子,
    //  抵押品的价值 除以 抵押品数量
    let health_factor = collateral_adjuested_for_liquidation_threshold / collateral.amount_minted;


    Ok(health_factor)
}


// 我们要获取sol的价值 
// pyth 上面的价格 * sol的数量
pub fn get_usd_value(
    amount_in_lamports: &u64,
    price_feed: &Account<PriceUpdateV2>,
) -> Result<u64> {
    // 
    let feed_id = get_feed_id_from_hex(FEED_SOL_TO_USD_ID)?;
    //
    // 获取价格数据
    let price = price_feed.get_price_no_older_than(&Clock::get()?, MAXIMUM_AGE, &feed_id)?;
    //如果价格不存在，返回错误
    require!(price.price> 0, CustomError::InvalidPriceFeed);     
    // 计算sol的价值
    let price_in_usd = price.price as u128 * PRICE_FEED_DECIMALS_ADJUSTMENT;
    // 算出美元的价格    
    let amount_in_usd = (*amount_in_lamports as u128 * price_in_usd) / (LAMPORTS_PER_SOL as u128);
    
    
    Ok(amount_in_usd as u64)
    
}

// 要清算的金额,转换成lamports
pub fn get_lamports_from_usd(
    price_feed: &Account<PriceUpdateV2>,
    amount_in_usd: &u64,
) -> Result<u64> {
    // 
    let feed_id = get_feed_id_from_hex(FEED_SOL_TO_USD_ID)?;
    //
    // 获取价格数据
    let price = price_feed.get_price_no_older_than(&Clock::get()?, MAXIMUM_AGE, &feed_id)?;
    //如果价格不存在，返回错误
    require!(price.price> 0, CustomError::InvalidPriceFeed); 

    let price_in_usd = price.price as u128 * PRICE_FEED_DECIMALS_ADJUSTMENT;

    let amount_in_lamports = (*amount_in_usd as u128 * (LAMPORTS_PER_SOL as u128)) /price_in_usd;
    Ok(amount_in_lamports as u64)
}