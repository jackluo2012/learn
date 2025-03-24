use std::io;
use rand::Rng;
fn main() {
    println!("Guess the number!");
    let secret_number = rand::thread_rng().gen_range(1..=10);
    println!("The secret number is: {}", secret_number);
    loop {
        
    
        println!("Please input your guess.");
        let mut guess = String::new();
        io::stdin().read_line(&mut guess)
            .expect("Failed to read line");
        let guess: i32 = match guess.trim().parse() {
            Ok(num) => num,
            Err(_) => {
                println!("Please enter a number!");
                0
            }
        };
        match guess.cmp(&secret_number) {
            std::cmp::Ordering::Less => println!("Too small!"),
            std::cmp::Ordering::Greater => println!("Too big!"),
            std::cmp::Ordering::Equal => {
                println!("You win!");
                break;
            },
            
        }
        println!("You guessed: {}", guess);
    }
}
