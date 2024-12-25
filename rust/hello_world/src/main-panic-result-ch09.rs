use std::fs::File;
use std::io::ErrorKind;
fn main(){
    {
    // panic!("crash and burn");
    }
    {
        // let v = vec![1, 2, 3];
        // // v goes out of scope here
        // v[99];
    }
    {
        let greeting_file_result = File::open("hello.txt");
        let greeting_file = match greeting_file_result {
            Ok(file) => file,
            Err(error) => match error.kind(){
                ErrorKind::NotFound => {
                    File::create("hello.txt").unwrap_or_else(|error| {
                        panic!("Problem creating the file: {:?}", error);
                    })
                },
                other_error => {
                    panic!("Problem opening the file: {:?}", other_error);
                }
            }, 
        };
    }
    {
        let greeting_file = File::open("hello.txt").unwrap_or_else(|error| {
            if error.kind() == ErrorKind::NotFound {
                File::create("hello.txt").unwrap_or_else(|error| {
                    panic!("Problem creating the file: {:?}", error);
                })
            }else {
                panic!("Problem opening the file: {:?}", error);
            }
        });
    }
    {
        let greeting_file = File::open("hello.txt").unwrap();
    
    }
    {
        let greeting_file = File::open("hello.txt").expect("hello.txt should be included in this project");
    }
    {
        use std::fs::File;
        use std::io::{self, Read};
        fn read_username_from_file() -> Result<String, io::Error> {
            let username_file_result = File::open("hello.txt");
            let mut username_file = match username_file_result {
                Ok(file) => file,
                Err(e) => return Err(e),
            };
            let mut s = String::new();
            match username_file.read_to_string(&mut s) {
                Ok(_) => Ok(s),
                Err(e) => Err(e),
            }
            
        }
        let username = read_username_from_file().expect("Failed to read username");
        println!("Username: {}", username);
    }
    {
        use std::fs::File;
        use std::io::{self, Read};
        fn read_username_from_file() -> Result<String, io::Error> {
            let mut username_file = File::open("hello.txt")?;
            let mut s = String::new();
            username_file.read_to_string(&mut s)?;
            // File::open("hello.txt")?.read_to_string(&mut s)?;
            Ok(s)
        }
        let username = read_username_from_file().expect("Failed to read username");
        println!("Username: {}", username);
    }
    {
        use std::fs::File;
        use std::io::{self, Read};
        fn read_username_from_file() -> Result<String, io::Error> {
            let mut s = String::new();
            File::open("hello.txt")?.read_to_string(&mut s)?;
            Ok(s)
        }
        let username = read_username_from_file().expect("Failed to read username");
        println!("Username: {}", username);
    }
    {
        use std::fs;
        use std::io;
        fn read_username_from_file() -> Result<String, io::Error> {
            fs::read_to_string("hello.txt")
        }
        let username = read_username_from_file().expect("Failed to read username");
        println!("Username: {}", username);
    }
    {
        fn last_char_of_first_line(text: &str) -> Option<char> {
            text.lines().next()?.chars().last()
        }
    }
    {
        use std::net::IpAddr;
        let home: IpAddr = "127.0.0.1".parse().expect("Hardcoded IP address should be valid");
    }
    {
        loop {
            let guess: i32 = match guess.trim().parse() {
                Ok(num) => num,
                Err(_) => continue,
            };
            if guess < 1 || guess > 100 {
                println!("The secret number is between 1 and 100.");
                continue;
            }
            match guess.cmp(&secret_number) {
                // --snip--
            }
        }
    }
}