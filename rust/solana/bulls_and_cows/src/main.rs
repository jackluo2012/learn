use rand::Rng;
use std::io;
fn main() {
    let mut rng = rand::rng();
    let secret_number  = rng.random_range(1..=101);
    let mut attempts = 0;
	println!("Please input a number: ");
	let mut guess = String::new();
	io::stdin().read_line(&mut guess).expect("Failed to read line");
}
