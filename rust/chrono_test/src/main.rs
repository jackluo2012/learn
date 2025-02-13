// use chrono::{TimeZone, Utc};
// use chrono_tz::US::Pacific;
// use chrono::DateTime; // 
use chrono::prelude::*;
use chrono::{NaiveDate, NaiveDateTime};
fn main() {
    // let time_str = DateTime::parse_from_str("2022-01-01 00:00:00", "%Y-%m-%d %H:%M:%S").unwrap();
    // println!("{}", time_str);
    let xxx = NaiveDateTime::parse_from_str("2025-01-13 21:00:09", "%Y-%m-%d %H:%M:%S").unwrap().timestamp_nanos();
    println!("xxx {}", xxx);
}
