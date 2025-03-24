
fn main() {

    let four = IpAddrKind::V4;
    let six = IpAddrKind::V6;
    //结构
    {
        let home = IpAddr{
            kind: IpAddrKind::V4,
            address:String::from("127.0.0.1")
        };
        let loopback = IpAddr {
            kind: IpAddrKind::V6,
            address:String::from("::1")
        };
        struct IpAddr{
            kind: IpAddrKind,
            address: String,
        }
    }
    //枚举
    {
        let home = IpAddr::V4(String::from("127.0.0.1")) ;
        let loopback = IpAddr::V6(String::from("::1"));
        enum IpAddr {
            V4(String),
            V6(String),
        }
    }
    {
        enum IpAddr {
            V4(u8, u8, u8, u8),
            V6(String),
        }
        let home = IpAddr::V4(127, 0, 0, 1);
        let loopback = IpAddr::V6(String::from("::1"));
    }
    {
        struct Ipv4Addr {
            // --snip--
        }
        struct Ipv6Addr {
            // --snip--
        }
        enum IpAddr {
            V4(Ipv4Addr),
            V6(Ipv6Addr),
        }
    }
    {
        enum Message{
            Quit,
            Move {x: i32, y: i32},
            Write(String),
            ChangeColor(i32, i32, i32),
        }
        impl Message {
            fn call(&self) {
                // --snip--
            }
        }
        let m = Message::Write(String::from("hello"));
        m.call();

    }
    {
        struct QuitMessage;// 类单元结构体
        struct MoveMessage {
            x: i32,
            y: i32,
        }
        struct WriteMessage(String); //元组结构体
        struct ChangeColorMessage(i32, i32, i32);// 元组结构体
    }
    {
        let some_number = Some(5);
        let some_string = Some("a string");
        let some_char = Some('c');
        let absent_number: Option<i32> = None;
    }
    {
        value_in_cents(Coin::Quarter(UsState::Alaska));
    }
    {
        fn plus_one(x: Option<i32>)-> Option<i32> {
            match x {
                None => None,
                Some(i) => Some(i+1),
            }
        }
        let five = Some(5);
        let six = plus_one(five);
        let none = plus_one(None);
    }
    {
        let dice_roll = 9;
        match dice_roll {
            3 => add_fancy_hat(),
            7 => remove_fancy_hat(),
            other => move_player(other),
        }
        fn add_fancy_hat(){}
        fn remove_fancy_hat(){}
        fn move_player(num_spaces:u8){}
    }
    {
        let dice_roll = 9;
        match dice_roll {
            3 => add_fancy_hat(),
            7 => remove_fancy_hat(),
            _ => reroll(),
        }
        fn add_fancy_hat(){}
        fn remove_fancy_hat(){}
        fn reroll(){}
    }
    {
        let dice_roll = 9;
        match dice_roll {
            3 => add_fancy_hat(),
            7 => remove_fancy_hat(),
            _ => (),
        }
        fn add_fancy_hat(){}
        fn remove_fancy_hat(){}
     
    }
    {
        let config_max = Some(3u8);
        match config_max {
            Some(max) => println!("The maxinum is configured to be {max}"),
            _ => (),
        }
    }
    {
        let config_max = Some(3u8);
        if let Some(max) = config_max {
            println!("The maximum is configured to be {max}");
        }
    }
    {
        let mut count =0 ;
        let coin = Coin::Penny;
        match coin {
            Coin::Quarter(state)=> println!("State quarter from {state:?}!"),
            _ => count +=1,
        }
    }
    {
        let mut count = 0;
        if let Coin::Quarter(state) = coin {
            println!("State quarter from {state:?}!");
        }else{
            count +=1;
        }
    }
}


enum IpAddrKind{
    V4,
    V6,
}
#[derive(Debug)]
enum UsState {
    Alabama,
    Alaska,
    // -- snip--
}
enum Coin {
    Penny,
    Nickel,
    Dime,
    Quarter(UsState),
}

fn value_in_cents(coin:Coin) -> u8 {
    match coin {
        Coin::Penny => {
            println!("Lucy penny!");
            1
        }
        Coin::Nickel =>5,
        Coin::Dime=>10,
        Coin::Quarter(state)=>{
            println!("State quarter from {state:?}!");
            25
        }
    }
}



