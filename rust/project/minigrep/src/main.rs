use std::env;
use std::process;
use  minigrep::Config;
fn main() {

    let args: Vec<String> = env::args().collect();
    // dbg!(args);
    // 读取要查询的字符串
    let config = Config::build(&args).unwrap_or_else(|err| {
        eprintln!("Problem parsing arguments: {err}");
        process::exit(1);
    });
    println!("Searching for: {}", config.query);
    // 读取文件路径
    println!("In file: {}", config.file_path);

    if let Err(e)  = minigrep::run(config) {
        eprintln!("Application error: {e}");
        // 退出程序
        process::exit(1);
    }

}