fn main(){
    
    {
        let number_list = vec![34, 50, 25, 100, 65];

        let mut largest = number_list[0];

        for item in &number_list {
            if item > &largest {
                largest = *item;
            }
        }

        println!("The largest number is {}", largest);

        let number_list = vec![102, 34, 6000, 89, 54, 2, 43, 8];
        let mut largest = number_list[0];

        for &item in &number_list {
            if item > largest {
                largest = item;
            }
        }

        println!("The largest number is {}", largest);
    }
    {
        let number_list = vec![34, 50, 25, 100, 65];

        let result = largest_number(&number_list);
        println!("The largest number is {}", result);

        let number_list = vec![102, 34, 6000, 89, 54, 2, 43, 8];
        let result = largest_number(&number_list);
        println!("The largest number is {}", result);
    }
    {
        let number_list = vec![34, 50, 25, 100, 65];

        let result = largest_i32(&number_list);
        println!("The largest number is {}", result);

        let char_list = vec!['y', 'm', 'a', 'q'];

        let result = largest_char(&char_list);
        println!("The largest char is {}", result);
    }
    {
        let number_list = vec![34, 50, 25, 100, 65];

        let result = largest(&number_list);
        println!("The largest number is {}", result);

        let char_list = vec!['y', 'm', 'a', 'q'];

        let result = largest(&char_list);
        println!("The largest char is {}", result);
    }
    {
        let integer = Point { x: 5, y: 10 };
        let float = Point { x: 1.0, y: 4.0 };
        println!("integer: {integer:?}, float: {float:#?}");
    }
    {
        struct Point<T> {
            x: T,
            y: T,
        }

        let p = Point { x: 5, y: 10 };
    }
    {
        struct Point<T, U> {
            x: T,
            y: U,
        }

        let p = Point { x: 5, y: 10.4 };
        println!("p.x = {}, p.y = {}", p.x, p.y);
    }
    {
        struct Point<T> {
            x: T,
            y: T,
        }
        impl<T> Point<T> {
            fn new(x: T, y: T) -> Self {
                Point { x, y }
            }
            fn x(&self) -> &T {
                &self.x
            }
        }
        let p = Point::new(5, 10);
        println!("p.x = {}", p.x())
    }
    {
        impl Point<f32> {
            fn distance_from_origin(&self) -> f32 {
                (self.x.powi(2) + self.y.powi(2)).sqrt()
            }
        }
    }
    {
        struct Point<X1, Y1> {
            x: X1,
            y: Y1,
        }
        impl <X1, Y1> Point<X1, Y1> {
            fn mixup<X2, Y2>(self, other: Point<X2, Y2>) -> Point<X1, Y2> {
                Point {
                    x: self.x,
                    y: other.y,
                }
            }
        }
        let p1 = Point { x: 5, y: 10.4 };
        let p2 = Point { x: "Hello", y: 'c' };

        let p3 = p1.mixup(p2);

        println!("p3.x = {}, p3.y = {}", p3.x, p3.y);
    }
    {
        use aggregator::{Summary, Tweet};
        let tweet = Tweet {
            username: String::from("horse_ebooks"),
            content: String::from(
                "of course, as you probably already know, people",
            ),
            reply: false,
            retweet: false,
        };
        println!("1 new tweet: {}", tweet.summarize());
    }
    {
        use aggregator::{Summary, NewsArticle};
        let article = NewsArticle {
            headline: String::from("Penguins win the Stanley Cup Championship!"),
            location: String::from("Pittsburgh, PA, USA"),
            author: String::from("Iceburgh"),
            content: String::from(
                "The Pittsburgh Penguins once again are the best \
                 hockey team in the NHL.",
            ),
        };
        println!("New article available! {}", article.summarize());
    }
    {
        use aggregator::{Summary, Tweet};
        let tweet = Tweet {
            username: String::from("horse_ebooks"),
            content: String::from(
                "of course, as you probably already know, people",
            ),
            reply: false,
            retweet: false,
        };
        println!("1 new tweet: {}", tweet.summarize());
    }
    {
        let string1 = String::from("long string is long");
        let string2 = "xyz";
        let result = longest(string1.as_str(), string2);
        println!("The longest string is {}", result);
        
    }
    {
        let string1 = String::from("long string is long");
        {
            let string2 = String::from("xyz");
            let result = longest(string1.as_str(), string2.as_str());
            println!("The longest string is {}", result);
        }
        println!("The longest string is {}", string1);
    }
    {
        let novel = String::from("Call me Ishmael. Some years ago...");
        let first_sentence = novel.split('.').next().expect("Could not find a '.'");
        
        let i = ImportantExcerpt {
            part: "Call me Ishmael. Some years ago...",
        };
    }
    {
        use std::fmt::Display;
        fn longest_with_an_announcement<'a, T>(x: &'a str, y: &'a str, ann: T) -> &'a str
        where
            T: Display,
        {
            println!("Announcement! {}", ann);
            if x.len() > y.len() {
                x
            } else {
                y
            }
        }
        let string1 = String::from("long string is long");
        let result = longest_with_an_announcement(string1.as_str(), string1.as_str(), "hello");
        println!("The longest string is {}", result);
    }
}
#[derive(Debug)]
struct Point<T> {
    x: T,
    y: T,
}
struct ImportantExcerpt<'a> {
    part: &'a str,
}
impl<'a> ImportantExcerpt<'a> {
    fn level(&self) -> i32 {
        3
    }
}

impl<'a> ImportantExcerpt<'a> {
    fn announce_and_return_part(&self, announcement: &str) -> &str {
        println!("Attention please: {}", announcement);
        self.part
    }
}

fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() {
        x
    } else {
        y
    }
}
fn largest<T: PartialOrd + Copy>(list: &[T]) -> T {
    let mut largest = list[0];

    for &item in list {
        if item > largest {
            largest = item;
        }
    }

    largest
}
fn largest_i32(list: &[i32]) -> &i32 {
    let mut largest = &list[0];

    for item in list {
        if item > largest {
            largest = item;
        }
    }

    largest
    
}
fn largest_char(list: &[char]) -> &char {
    let mut largest = &list[0];

    for item in list {
        if item > largest {
            largest = item;
        }
    }

    largest
}
fn largest_number(list: &[i32]) -> i32 {
    let mut largest = list[0];

    for &item in list {
        if item > largest {
            largest = item;
        }
    }

    largest
}