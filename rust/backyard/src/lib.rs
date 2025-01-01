//! # Art
//! 
//! A library for modeling artistic concepts.
pub mod kinds {
    /// The primary colors according to the RYB color model.
    pub enum PrimaryColor {
        Red,
        Yellow,
        Blue,
    }

    /// The secondary colors according to the RYB color model.
    pub enum SecondaryColor {
        Orange,
        Green,
        Purple,
    }

    /// The tertiary colors according to the RYB color model.
    pub enum TertiaryColor {
        RedOrange,
        YellowGreen,
        BlueGreen,
        PurpleBlue,
        PurpleRed,
    }
}

pub mod utils {
    use crate::kinds::*;
    /// Combines two primary colors in equal parts.
    /// a secondary color.
    pub fn mix(primary_color1: PrimaryColor, primary_color2: PrimaryColor) -> SecondaryColor {
        // --snip--
        SecondaryColor::Orange
    }

    
}

pub trait Messager {
    fn send(&self, msg: &str);
}
pub struct LimitTracker<'a, T: Messager> {
    messenger: &'a T,
    value: u32,
    max: u32,
}
impl <'a, T> LimitTracker<'a, T>
where
    T: Messager,
{
    pub fn new(messenger: &T, max: u32) -> LimitTracker<T> {
        LimitTracker {
            messenger,
            value: 0,
            max,
        }
    }
    pub fn set_value(&mut self, value: u32) {
        self.value = value;
        let percentage_of_max = self.value as f64 / self.max as f64;
        if percentage_of_max >= 1.0 {
            self.messenger.send("Error: You are over your quota!");
        } else if percentage_of_max >= 0.9 {
            self.messenger.send("Urgent warning: You've used up over 90% of your quota!");
        } else if percentage_of_max >= 0.75 {
            self.messenger.send("You are under your quota!");
        }
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    use std::cell::RefCell;
    struct MockMessenger {
        sent_messages: RefCell<Vec<String>>,
    }
    impl MockMessenger {
        fn new() -> MockMessenger {
            MockMessenger {
                sent_messages:RefCell::new(vec![]),
            }
        }
    }
    impl Messager for MockMessenger {
        fn send(&self, message: &str) {
            self.sent_messages.borrow_mut().push(String::from(message));
        }
    }
    #[test]
    fn it_sends_an_over_75_percent_warning_message() {
        let mock_messenger = MockMessenger::new();
        let mut limit_tracker = LimitTracker::new(&mock_messenger, 100);
        limit_tracker.set_value(80);
        assert_eq!(mock_messenger.sent_messages.borrow().len(), 1);
    }
    #[test]
    fn it_works() {
        assert_eq!(2 + 2, 4);
    }
}