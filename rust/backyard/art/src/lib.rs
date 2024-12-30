//! # Art
//! 
//! A library for modeling artistic concepts.
pub mod kinds{
    /// Primary colors that can be used by an artist
    pub enum PrimaryColor {
        Red,
        Yellow,
        Blue,
    }

    /// Secondary colors that can be used by an artist
    pub enum SecondaryColor {
        Orange,
        Green,
        Purple,
    }

    /// All colors an artist can use
    pub enum Color {
        PrimaryColor(PrimaryColor),
        SecondaryColor(SecondaryColor),
    }
}

pub mod utils {
    use crate::kinds::{PrimaryColor, SecondaryColor, Color};

    /// Combines two primary colors in different ways
    /// 
    /// # Examples
    /// ```
    /// use art::utils::mix;
    /// use art::kinds::{PrimaryColor, Color};
    /// 
    /// let c = mix(PrimaryColor::Red, PrimaryColor::Yellow);
    /// 
    /// assert_eq!(c, Color::SecondaryColor(SecondaryColor::Orange));   
    /// ```
    pub fn mix(c1: PrimaryColor, c2: PrimaryColor) -> SecondaryColor {
        SecondaryColor::Orange
    }
}