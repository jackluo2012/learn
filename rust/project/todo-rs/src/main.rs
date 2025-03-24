mod database;

use std::env;
use database::{Database,Record};

fn main() {
    // 获取命令行参数
    let args: Vec<String> = env::args().collect();
    //如果小于2个参数，则打印帮助信息并退出程序
    if args.len() < 2 {
        println!("Usage: {} <input_file>", args[0]);
        return;
    }
    let command: &String = &args[1];

    let mut db= Database::open("rodo.db");
    match command.as_str() {
        "--help" | "-h" => {
            println!("This program demonstrates how to use the 'match' keyword in Rust.");
            println!("It takes one argument, which is the name of a file to read.");
            println!("The program will then print out the contents of the file.");
        },
        "add" => {
            if args.len() != 3 {
                println!("Usage: rodo add [contents]");
                return;
            }
            let content = &args[2..].join(" ");
            let id = db.read_records().last().map(|r| r.id + 1).unwrap_or(1);
            let rc = Record{
                id,
                content: content.to_string(),
            };
            db.add_record(&rc);

            println!("Add");
        }
        "rm" => {
            if args.len() != 3 {
                println!("Usage: rodo rm [id]");
                return;
            }
            let id = args[2].parse::<i32>().unwrap();
            db.remove_record(id);
            println!("Delete");            
        }
        "ls"=> {
            let records = db.read_records();
            for record in records {
                println!("⬜️ {}: {}",record.id,record.content);
            }            
            println!("List");
        }
        _ => {
            println!("Unknown command: {}",command)
        }
    }
}
