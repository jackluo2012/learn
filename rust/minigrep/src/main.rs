use std::env;
use std::fs;
use std::process;
use minigrep::Config;

fn main() {
    // println!("Hello, world!");
    let args: Vec<String> = env::args().collect();
    {
        let config = parse_config(&args);
        if let Err(e) = minigrep::run(config) {
            eprintln!("Application error: {}", e);
            process::exit(1);
        }
    }
    println!("-------------------------------------");
    {
        let config = Config::build(&args).unwrap_or_else(|err| {
            eprintln!("Problem parsing arguments: {}", err);
            process::exit(1);        
        });
        if let Err(e) = minigrep::run(config) {
            eprintln!("Application error: {}", e);
            process::exit(1);
        }
    }
}



fn parse_config(args: &[String]) -> Config {
    let query = args[1].clone();
    let file_path = args[2].clone();
    let ignore_case = env::var("IGNORE_CASE").is_ok();

    Config { query, file_path, ignore_case }
}
