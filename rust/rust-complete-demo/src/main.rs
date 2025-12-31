use rustdx_complete::tcp::stock::FinanceInfo;
use rustdx_complete::tcp::stock::Kline;
use rustdx_complete::tcp::stock::MinuteTime;
use rustdx_complete::tcp::stock::SecurityQuotes;
use rustdx_complete::tcp::stock::Transaction;
use rustdx_complete::tcp::{Tcp, Tdx};
fn main() -> Result<(), Box<dyn std::error::Error>> {
    realtime_quotes_multi()?;
    // realtime_quotes()?;
    // index_quotes()?;
    // daily_quotes()?;
    // financial_info()?;
    // time_series()?;
    // ticks()?;
    Ok(())
}

// 获取多只股票的实时快照数据
fn realtime_quotes_multi() -> Result<(), Box<dyn std::error::Error>> {
    let mut tcp = Tcp::new()?;
    let mut quotes = SecurityQuotes::new(vec![
        (0, "000001"), // 平安银行（深市）
        (1, "600000"), // 浦发银行（沪市）
        (1, "600036"), // 招商银行（沪市）
    ]);

    quotes.recv_parsed(&mut tcp)?;

    for quote in quotes.result() {
        // println!("股票代码: {}", quote.code);
        // println!("当前价: {:.2}", quote.price);
        // println!("昨收: {:.2}", quote.preclose);
        // println!("今开: {:.2}", quote.open);
        // println!("最高: {:.2}", quote.high);
        // println!("最低: {:.2}", quote.low);
        // println!("成交量: {:.0}", quote.vol);
        // println!("成交额: {:.0}", quote.amount);
        // println!("买一: {:.2} × {:.0}", quote.bid1, quote.bid1_vol);
        // println!("卖一: {:.2} × {:.0}", quote.ask1, quote.ask1_vol);
        // println!("涨跌幅: {:.2}%", quote.change_percent);
        println!("完整: {:?}", quote);
        println!();
    }
    Ok(())
}

fn realtime_quotes() -> Result<(), Box<dyn std::error::Error>> {
    let mut tcp = Tcp::new()?;

    // 获取多只股票的实时行情
    let mut quotes = SecurityQuotes::new(vec![
        (0, "000001"), // 平安银行（深市）
        (1, "600000"), // 浦发银行（沪市）
    ]);

    quotes.recv_parsed(&mut tcp)?;

    for quote in quotes.result() {
        println!("{}: {} - 当前价: {}", quote.code, quote.name, quote.price);
    }
    Ok(())
}

// 获取指数行情
fn index_quotes() -> Result<(), Box<dyn std::error::Error>> {
    let mut tcp = Tcp::new()?;

    // 获取主要指数行情
    let mut quotes = SecurityQuotes::new(vec![
        (1, "000001"), // 上证指数
        (0, "399001"), // 深证成指
        (1, "000300"), // 沪深300
    ]);

    quotes.recv_parsed(&mut tcp)?;

    for quote in quotes.result() {
        println!(
            "{}: {} (涨跌: {}%)",
            quote.code, quote.price, quote.change_percent
        );
    }
    Ok(())
}

//获取日线数据
fn daily_quotes() -> Result<(), Box<dyn std::error::Error>> {
    let mut tcp = Tcp::new()?;
    let mut kline = Kline::new(1, "600000", 9, 0, 10); // 沪市、浦发银行、日线、从0开始获取10条

    kline.recv_parsed(&mut tcp)?;

    for bar in kline.result() {
        println!(
            "{:?} : 开({}) 高({}) 低({}) 收({})",
            bar.dt, bar.open, bar.high, bar.low, bar.close
        );
    }
    Ok(())
}

// 获取财务信息
fn financial_info() -> Result<(), Box<dyn std::error::Error>> {
    let mut tcp = Tcp::new()?;
    let mut finance = FinanceInfo::new(0, "000001"); // 深市、平安银行

    finance.recv_parsed(&mut tcp)?;

    let info = &finance.result()[0];
    println!("股票代码: {}", info.code);
    println!("总股本: {:.0} 股", info.zongguben);
    println!("净资产: {:.0} 元", info.jingzichan);
    println!("净利润: {:.0} 元", info.jinglirun);
    Ok(())
}
// 获取分时数据
fn time_series() -> Result<(), Box<dyn std::error::Error>> {
    let mut tcp = Tcp::new()?;
    let mut minute = MinuteTime::new(0, "000001"); // 深市、平安银行

    minute.recv_parsed(&mut tcp)?;

    for data in minute.result().iter().take(10) {
        // 只打印前10条
        println!(" 价格={} 成交量={}", data.price, data.vol);
    }
    Ok(())
}
//获取逐笔成交
fn ticks() -> Result<(), Box<dyn std::error::Error>> {
    let mut tcp = Tcp::new()?;
    let mut transaction = Transaction::new(0, "000001", 0, 10); // 深市、平安银行、从第0条开始

    transaction.recv_parsed(&mut tcp)?;

    for data in transaction.result().iter().take(5) {
        // 只打印前5笔
        println!(
            "{} : 价格={} 成交量={} 买卖方向={}",
            data.time, data.price, data.vol, data.buyorsell
        );
    }
    Ok(())
}
