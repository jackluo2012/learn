use crate::garden::vegetables::Asparagus;
pub mod garden;
use std::collections::HashMap;
use rand::Rng;
use std::{cmp::Ordering, io};

fn main() {
    let plant = Asparagus {};
    println!("I'm growing {plant:?}!");
    let mut map = HashMap::new();
    map.insert(1, 2);
    let secret_number = rand::thread_rng().gen_range(1..101);
}
