use pyo3::prelude::*;



/// A Python module implemented in Rust.
#[pymodule]
mod guessing_game {
    use pyo3::prelude::*;
    use std::io;
    use std::cmp::Ordering;
    /// Formats the sum of two numbers as string.
    #[pyfunction]
    fn guess_the_number() {
        println!("Guess the number!");

        let secret_number = rand::random_range(1..101);

        loop {
            println!("Please input your guess.");
            let mut guess = String::new();

            io::stdin()
            .read_line(&mut guess)
            .expect("Failed to read line");

            let guess: u32 = match guess.trim().parse() {
                Ok(num) => num,
                Err(_) => continue,
            };

            println!("You guessed: {}", guess);

            match guess.cmp(&secret_number) {
                Ordering::Less => println!("Too small!"),
                Ordering::Greater => println!("Too big!"),
                Ordering::Equal => {
                    println!("You win!");
                    break;
                }
            }
    }
}
}
