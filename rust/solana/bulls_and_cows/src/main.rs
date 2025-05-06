use rand::Rng;
use std::io;
use std::cmp::Ordering;
fn main() {
    let mut rng = rand::rng();
    let secret_number  = rng.random_range(1..=101);
    let mut attempts = 0;
	loop{
        println!("Please input a number: ");
        let mut guess = String::new();
        io::stdin().read_line(&mut guess).expect("Ops! Something goes wrong");
        // 去掉空格 
        let guess = match guess.trim().parse::<u32>() {
            Ok(num) => num,
            Err(_) => {
                print!("Please input a number!");
                continue;
            },
        };
        if guess <1 || guess > 10 {
            println!("Please input a number between 1 and 10!");
            continue;
        }
        match guess.cmp(&secret_number) {
            Ordering::Less => {
                println!("Too small!");
                
            }
            Ordering::Greater => {
                println!("Too big!");
                
            }
            Ordering::Equal => {
                println!("Congratulation you're right!");
                println!("tips: you have tried {} times", attempts);
                break;
            }
        }
        if attempts > 5{
            println!("tips: you have tried {} times, try again!",attempts)
        }
        if attempts == 10 {
            println!("You have tried 10 times, game over");
            break;
        }  
        



        attempts += 1;
    }
}
