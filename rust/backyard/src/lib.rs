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