pub struct Guess {
    value: i32,
}

impl Guess {
    pub fn new(value: i32) -> Guess {
        if value < 1 {
            panic!("Guess value must be greater than or equal to 1, got {}.", value);
        } 
        Guess { value }
    }

    pub fn value(&self) -> i32 {
        self.value
    }
}