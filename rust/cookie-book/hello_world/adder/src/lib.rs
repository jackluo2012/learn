pub fn add(left: u64, right: u64) -> u64 {
    left + right
}
pub fn add_two(a: i32) -> i32 {
    a + 2
}
pub fn add_three(a: i32) -> i32 {
    a + 3
}
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn it_works() {
        let result = add(2, 2);
        assert_eq!(result, 4);
    }
    #[test]
    fn exploration(){
        let result = add(2, 2);
        assert_eq!(result, 4);
    }
    #[test]
    fn another(){
        // panic!("Make this test fail");
    }
    #[test]
    fn larger_can_hold_smaller(){
        let larger = Rectangle{width: 8, height: 7};
        let smaller = Rectangle{width: 5, height: 1};
        assert!(larger.can_hold(&smaller));
    }
    #[test]
    fn smaller_cannot_hold_larger(){
        let larger = Rectangle{width: 8, height: 7};
        let smaller = Rectangle{width: 5, height: 1};
        assert!(!smaller.can_hold(&larger));
    }
    #[test]
    fn it_adds_two(){
        assert_eq!(4, add_two(2));
    }
    
    pub fn greeting(name: &str) -> String {
        format!("Hello {}!", name)
    }
    #[test]
    fn greeting_contains_name() {
        let result = greeting("Carol");
        assert!(result.contains("Carol"));
    }
    pub fn greeting_two(name: &str) -> String {
        let greeting = format!("Hello !");
        greeting
    }
    #[test]
    fn greeting_two_contains_name() {
        let result = greeting_two("Carol");
        assert!(result.contains("Carol"));
    }
    #[test]
    fn greeting_contains_name_two(){
        let result = greeting_two("Carol");
        assert!(
            result.contains("Carol"),
            "Greeting did not contain name, value was `{result}`"
        );
    }
    #[test]
    #[should_panic(expected = "Guess value must be less than or equal to 100")]
    fn greater_than_100(){
        Guess::new(200);
    }
    #[test]
    fn it_works_two() ->Result<(),String>{
        let result = add(2, 2);
        if result == 5 {
            Ok(())
        }else {
            Err(String::from("addition was not correct"))
        }
    }
    #[test]
    fn this_test_will_pass() {
        let value = prints_and_returns_10(4);
        assert_eq!(10, value);
    }
    #[test]
    fn this_test_will_fail() {
        let value = prints_and_returns_10(8);
        assert_eq!(5, value);
    }
    #[test]
    fn this_test_will_fail_two() {
        let value = integer_adder(8, 2);
        assert_eq!(5, value);
    }
}
fn integer_adder(a: i32, b: i32) -> i32 {
    a + b
}
fn prints_and_returns_10(a: i32) -> i32 {
    println!("I got the value {}", a);
    10
}
#[derive(Debug)]
struct Rectangle {
    width: u32,
    height: u32,
}

impl Rectangle {
    fn can_hold(&self, other: &Rectangle) -> bool {
        self.width > other.width && self.height > other.height
    }
}
pub struct Guess {
    value: i32,
}
impl Guess {
    pub fn new(value: i32) -> Guess {
        if value > 1 {
            panic!(
                "Guess value must be greater than or equal to 1, got {value}."
            );
        } else if value < 100 {
            panic!(
                "Guess value must be less than or equal to 100, got {value}."
            );
        }

        Guess { value }
    }
}