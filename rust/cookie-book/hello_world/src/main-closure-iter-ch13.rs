use std::thread;
#[derive(Debug,PartialEq,Copy,Clone)]
enum ShirtColor {
    Red,
    Blue,
}

struct Inventory {
    shirts: Vec<ShirtColor>,
}

impl Inventory {
    fn giveaway(&self, user_preferenc: Option<ShirtColor>) -> ShirtColor {
        user_preferenc.unwrap_or_else(|| self.most_stocked())
    }

    fn most_stocked(&self) -> ShirtColor {
        let mut num_red = 0;
        let mut num_blue = 0;

        for color in &self.shirts {
            match color {
                ShirtColor::Red => num_red += 1,
                ShirtColor::Blue => num_blue += 1,
            }
        }

        if num_red > num_blue {
            ShirtColor::Red
        } else {
            ShirtColor::Blue
        }
    }
}


fn main() {
    {
    let store = Inventory {
        shirts: vec![ShirtColor::Blue, ShirtColor::Blue, ShirtColor::Red],
    };

    let user_pref1 = Some(ShirtColor::Red);
    let giveaway1 = store.giveaway(user_pref1);
    println!("The user with preference {:?} gets {:?}", user_pref1, giveaway1);

    let user_pref2 = None;
    let giveaway2 = store.giveaway(user_pref2);
    println!("The user with preference {:?} gets {:?}", user_pref2, giveaway2);
    

    }
    {
        use std::time::Duration;
        

        let expensive = |price: u32| -> u32 {
            println!("calculating slowly...");
            // thread::sleep(Duration::from_secs(0.0002));
            price + 1
         };
         println!("{}", expensive(5));
    }
    {
        fn add_one(x: i32) -> i32 {
            x + 1
        }
        let add_one_v1 = |x: i32| -> i32 { x + 1 };
        let add_one_v2 = |x: u32| x + 1;
        
    }
    {
        let example_closure = |x: u32| x; // |x| x 是闭包，它接受一个参数 x，并返回 x
        let s = example_closure(5); // 调用闭包，将返回值赋给变量 s
    }
    {
        let list = vec![1, 2, 3];
        println!("Before defining closure: {:?}", list);
        let only_borrows = || println!("From closure: {:?}", list);
        println!("Before calling closure: {:?}", list);
        only_borrows();
        println!("After calling closure: {:?}", list);
    }
    {
        let mut list = vec![1, 2, 3];
        println!("Before defining closure: {:?}", list);
        println!("Before defining closure: {:?}", list);
        let mut borrows_mutably = || list.push(7);
        borrows_mutably();
        println!("After calling closure: {:?}", list);
    }
    {
        let list = vec![1, 2, 3];
        println!("Before defining closure: {:?}", list);
        thread::spawn(move || println!("From thread: {:?}", list)).join().unwrap();
    }
    {
        let mut list = [
            Rectangle { width: 10, height: 1 },
            Rectangle { width: 3, height: 5 },
            Rectangle { width: 7, height: 12 },
        ];

        list.sort_by_key(|r| r.width);
        println!("{:?}", list);
    }
    {
        let mut list = [
            Rectangle { width: 10, height: 1 },
            Rectangle { width: 3, height: 5 },
            Rectangle { width: 7, height: 12 },
        ];
        let mut sort_opeartor = vec![];
        let value = String::from("closure called");

        list.sort_by_key(|r| {
            sort_opeartor.push(value.clone());
            r.width
        });
        println!("{:?}", list);
    }
    {
        let mut list = [
            Rectangle { width: 10, height: 1 },
            Rectangle { width: 3, height: 5 },
            Rectangle { width: 7, height: 12 },
        ];
        let mut num_sort_operations = 0;
        list.sort_by_key(|r| {
            num_sort_operations += 1;
            r.width
        });
        println!("{list:#?},sorted in {num_sort_operations} operations");
    }

    // iter() 方法返回一个迭代器，它会对集合中的每个元素调用闭包，并返回一个包含闭包返回值的迭代器
    {
        let list = vec![1, 2, 3];
        let sum: u32 = list.iter().sum();
        println!("Sum: {sum}");
        let v1_iter = list.iter();
        for i in v1_iter {
            println!("i: {i}");
        }
    }
    {
       let v1: Vec<i32> = vec![1, 2, 3];
       v1.iter().map(|i| i + 1).for_each(|i| println!("i: {i}"));
    }
    {
        let v1: Vec<i32> = vec![1, 2, 3];
        let v2: Vec<_> = v1.iter().map(|i| i + 1).collect();
        println!("v2: {:?}", v2);
    }
}
#[derive(Debug)]
struct Rectangle {
    width: u32,
    height: u32,
}
