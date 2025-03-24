
fn main() {
    {
        // 最喜欢的颜色
        let favorite_color: Option<&str> = None;
        // 是否是星期二
        let is_tuesday = false;
        // 年龄 把一个字符串 解析成一个u8
        let age: Result<u8, _> = "34".parse();

        if let Some(color) = favorite_color {
            println!("Using your favorite color, {}, as the background", color);
        } else if is_tuesday {
            println!("Tuesday is green day!");
        } else if let Ok(age) = age {
            if age > 30 {
                println!("Using purple as the background color");
            } else {
                println!("Using orange as the background color");
            }
        } else {
            println!("Using blue as the background color");
        }
    }
    {
        let (tx,rx) = std::sync::mpsc::channel();
        std::thread::spawn(move || {
            for i in 0..10 {
                tx.send(i).unwrap();    
            }
            
        });
        while let Ok(value) = rx.recv() {
            println!("{}",value);
        };
    }
    {
        let v = vec!['a', 'b', 'c'];
        //适配一个迭代器来产生一个值和其在迭代器中的索引
        for (index, value) in v.iter().enumerate() {
            println!("{} is at index {}", value, index);
        }
    }
    {
        fn print_coordinates(&(x,y): &(i32, i32)) {
            println!("Current location: ({}, {})", x, y);
        }
        let point = (3, 5);
        print_coordinates(&point);
        println!("{}",point.0)
    }
    {
        let x = 1;
        match x {
            1 => println!("one"),
            2 => println!("two"),
            3 => println!("three"),
            _ => println!("anything else")
        }
    }
    {
        let x = Some(5);
        let y = 10;
        match x {
            Some(50) => println!("Got 50"),
            Some(y) => println!("Matched, y = {:?}", y),
            _ => println!("Default case, x = {:?}", x),
        }
    }
    {
        let x = 4;
        match x {
            1 | 2 | 3 => println!("One of 1, 2, or 3"),
            4 => println!("Four"),
            _ => println!("Something else"),
        }
    }
    {
        let x = 5;
        match x {
            1 ..= 5 => println!("One through five"),
            _ => println!("Something else"),
        }
    }
    {
        let x = 'c';

        match x {
            'a'..='j' => println!("early ASCII letter"),
            'k'..='z' => println!("late ASCII letter"),
            _ => println!("something else"),
        }
    
    }
    {
        let p = Point { x: 0,y: 7 };
        let Point { x:a, y:b } = p;
        assert_eq!(0, a);
        assert_eq!(7, b);
    }
    {
        let p = Point { x: 0,y: 7 };
        let Point { x, y } = p;
        assert_eq!(0, x);
        assert_eq!(7, y);
    }
    {
        let p = Point { x: 0,y: 7 };
        match p {
            Point { x, y: 0 } => println!("On the x axis at {}", x),
            Point { x: 0, y } => println!("On the y axis at {}", y),
            Point { x, y } => println!("On neither axis: ({}, {})", x, y),
        }
    }
    {
        let msg = Message::ChangeColor(0, 160, 255);
        match msg {
            Message::Quit => println!("The Quit variant has no data to destructure."),
            Message::Move { x, y } => println!("Move in the x direction {} and in the y direction {}", x, y),
            Message::Write(text) => println!("Text message: {}", text),
            Message::ChangeColor(r, g, b) => println!("Change the color to red {}, green {}, and blue {}", r, g, b),
        }
    }
    {
        enum Color {
            Rgb(i32, i32, i32),
            Hsv(i32, i32, i32),
        }
        enum Message1 {
            Quit,
            Move { x: i32, y: i32 },
            Write(String),
            ChangeColor(Color),
        }
        let msg = Message1::ChangeColor(Color::Hsv(0, 160, 255));
        match msg {
            Message1::ChangeColor(Color::Rgb(r, g, b)) => {
                println!("Change color to red {}, green {}, and blue {}", r, g, b);
            },
            Message1::ChangeColor(Color::Hsv(h, s, v)) => {
                println!("Change color to hue {}, saturation {}, and value {}", h, s, v);
            },
            _ => (),
        }
    }
    {
        let ((feet,inches),Point{ x, y }) = ((3, 10), Point { x: 3, y: -10 });
    }
    {
        fn foo(_:i32,y:i32) {
            println!("This code only uses the y parameter: {}", y);
        }
        foo(3, 4);
    }
    {
        let mut setting_value = Some(5);
        let new_setting = Some(10);
        match (setting_value, new_setting) {
            (Some(_), Some(_)) => {
                setting_value = new_setting;
            },
            _ => {
                
            },
        }
        println!("Setting is: {:?}", setting_value);
    }
    {
        let numbers = (2, 4, 8, 16, 32);

        match numbers {
            (first, _, third, _, fifth) => {
                println!("Some numbers: {first}, {third}, {fifth}")
            }
        }
    
    }
    {
        let s = Some(String::from("Hello!"));

        if let Some(_) = s {
            println!("found a string");
        }
    
        println!("{s:?}");
    
    }
    {
        struct Point {
            x: i32,
            y: i32,
            z: i32,
        }
        let origin = Point { x: 0, y: 0, z: 0 };

        match origin {
            Point { x, .. } => println!("x is {}", x),
        }
    }
    {
        let numbers = (2, 4, 8, 16, 32);

        match numbers {
            (first, .., last) => {
                println!("Some numbers: {first}, {last}")
            }
        }
    }
    {
        let num = Some(4);

        match num {
            Some(x) if x % 2 == 0 => println!("The number {} is even", x),
            Some(x) => println!("The number {} is odd", x),
            None => (),
        }
    }
    {
        let x = Some(5);
        let y = 10;

        match x {
            Some(50) => println!("Got 50"),
            Some(n) if n == y => println!("Matched, y = {y}"),
            Some(n) => println!("Matched, n = {n}"),
            None => println!("Matched None"),
        }
    }
    {
        let x = 4;
        let y = false;

        match x {
            // 这个匹配条件表明此分支值匹配 
            // x 值为 4、5 或 6 同时 y 为 true 的情况
            // (4 | 5 | 6) if y
            4 | 5 | 6 if y => println!("yes"),
            _ => println!("no"),
        }
    }
    {
        enum Message {
            Hello { id: i32 },
        }

        let msg = Message::Hello { id: 5 };

        match msg {
            // 通过在 3..=7 之前指定 id_variable @，
            // 我们捕获了任何匹配此范围的值并同时测试其值匹配这个范围模式。
            Message::Hello { id: id_variable @ 3..=7 } => {
                println!("Found an id in range: {}", id_variable)
            },
            Message::Hello { id: 10..=12} =>{
                println!("Found an id in another range")
            }
            Message::Hello { id } => {
                println!("Found some other id: {}", id)
            },
        }
    }
}
enum Message {
    Quit,
    Move { x: i32, y: i32 },
    Write(String),
    ChangeColor(i32, i32, i32),
}
struct Point {
    x: i32,
    y: i32,
}
