use std::error::Error;
use std::{fs,env};
pub struct Config {
    pub query: String,
    pub file_path: String,
    pub case_sensitive: bool,
}

impl Config {
    pub fn new(query: String, file_path: String, case_sensitive: bool) -> Config {
        Config { query, file_path, case_sensitive }
    }
}
impl Config {
    pub fn build(args: &[String]) -> Result<Config, &'static str> {
        if args.len() < 3 {
            return Err("Not enough arguments. Usage: <program> <query> <file_path> <case_sensitive (true/false)>");
        }
        let query = &args[1];
        let file_path = &args[2];
        // 检查是否设置了环境变量 CASE_INSENSITIVE
        let case_sensitive = env::var("CASE_INSENSITIVE").map_or(false, |v| v.to_lowercase() == "true");
        Ok(Config { query: query.to_string(), file_path: file_path.to_string(), case_sensitive })
    }

    pub fn build_from_args_iterator(mut  args:  impl Iterator<Item = String>) -> Result<Config, &'static str> {
        // 第一个是程序的名称，所以跳过
        args.next();
        let query = match args.next() {
            Some(arg) => arg,
            None => return Err("Missing query argument"),
        };
        let file_path = match args.next() {
            Some(arg) => arg,
            None => return Err("Missing file path argument"),
        };
        // 检查是否设置了环境变量 CASE_INSENSITIVE
        let case_sensitive = env::var("CASE_INSENSITIVE").map_or(false, |v| v.to_lowercase() == "true");
        Ok(Config { query, file_path, case_sensitive })
    }
}

pub fn run(config: Config) -> Result<(), Box<dyn Error>> {
    let contents = fs::read_to_string(config.file_path)?;
    let results = if  config.case_sensitive {
        search(&config.query, &contents)
    } else {
        search_case_insensitive(&config.query, &contents)
    };

    for line in results {
        println!("{}", line);
    }
    Ok(())
}

pub fn search<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {

    let mut results = Vec::new();
    for line in contents.lines() {
        // 是否包含待查询的 query
        if line.contains(query) {
            results.push(line);
        }
    }

    results
}

pub fn  search_case_insensitive<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {
    let query = query.to_lowercase();
    let mut results = Vec::new();

    for line in contents.lines() {
        if line.to_lowercase().contains(&query) {
            results.push(line);
        }
    }

    results
}

pub fn search_iterator<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {
    contents.lines().filter(move |line| line.contains(query)).collect()
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn one_result() {
        let query = "duct";
        let contents = "\
Rust:
safe, fast, productive.
Pick three.";

        assert_eq!(vec!["safe, fast, productive."], search(query, contents));
    }

    #[test]
    fn case_insensitive() {
        let query = "rUsT";
        let contents = "\
Rust:
safe, fast, productive.
Pick three.
Trust me.";

        assert_eq!(
            vec!["Rust:", "Trust me."],
            search_case_insensitive(query, contents)
        );
    }   

}