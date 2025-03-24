use std::slice;
use std::fmt;
use std::ops::Add; // 使用Add trait
use hello_macro::HelloMacro; // 使用HelloMacro宏
fn main() {
    {
        // 从引用同时创建不可变和可变裸指针   
        let mut num =5;
        let r1 = &num as *const i32;
        let r2 = &mut num as *mut i32;
    }
    {
        let address = 0x01234usize;
        let r = address as *const i32;
    }
    {
        let mut num = 5;
        let r1 = &num as *const i32;
        let r2 = &mut num as *mut i32;
        // let r2 = 10 as *mut i32;
        unsafe {
            println!("r1 is: {}", *r1); // 5

            println!("r2 is: {}", *r2); // 5
        }
    }
    {
        unsafe fn dangerous(){}
        unsafe {
            dangerous();
        }
    }
    {

        let mut v = vec![1,2,3,4,5,6];
        let r = &mut v[..];

        let (a,b) = r.split_at_mut(3);
        assert_eq!(a, &mut[1,2,3]);
        assert_eq!(b, &mut[4,5,6])  ;
    }
    {
        let mut v = vec![1,2,3,4,5,6];
        let r = &mut v[..];

        fn split_at_mut(slice: &mut [i32], mid: usize) -> (&mut [i32], &mut [i32]) {
            let len = slice.len();
            let (left, right) = slice.split_at_mut(mid);
            assert_eq!(left.len() + right.len(), len);
            (left, right)
        }

        let (a,b) = split_at_mut(&mut v,3);
        assert_eq!(a, &mut[1,2,3]);
        assert_eq!(b, &mut[4,5,6])  ;

        
        println!("{:?}",a);
        println!("{:?}",b);
    }
    {
        let mut v = vec![1,2,3,4,5,6];
        let r = &mut v[..];

        fn split_at_mut(slice: &mut [i32], mid: usize) -> (&mut [i32], &mut [i32]) {
            let len = slice.len();
            // 返回一个 *mut i32 类型的裸指针
            let ptr = slice.as_mut_ptr(); // 获取可变引用的裸指针
            
            assert!(mid <= len);

            unsafe {
                (
                    slice::from_raw_parts_mut(ptr, mid), 
                // 我们保持索引 mid 位于 slice 中的断言。接着是不安全代码：
                // slice::from_raw_parts_mut 函数获取一个裸指针和一个长度来创建一个 slice。
                // 这里使用此函数从 ptr 中创建了一个有 mid 个项的 slice。之后在 ptr 上调用 add 方法
                // 并使用 mid 作为参数来获取一个从 mid 开始的裸指针，
                // 使用这个裸指针并以 mid 之后项的数量为长度创建一个 slice。
                slice::from_raw_parts_mut(ptr.add(mid), len - mid),
                )// 使用add方法获取指针的偏移量
            }
        }
    }
    {
        extern "C" {
            fn abs(input: i32) -> i32;
        }
        unsafe {
            println!("Absolute value of -3 according to C: {}", abs(-3));
        }
    }
    {
#[no_mangle]
pub extern "C" fn call_from_c() {
    println!("Just called a Rust function from C!");
}
    }
    {
        println!("name is : {HELLO_WORLD}");
    }
    {
        add_to_count(3);
        unsafe {
            println!("COUNTER: {}", COUNTER);
        }
    }
    {
        assert_eq!(Point {x: 1, y: 0} + Point {x: 2, y: 3}, Point {x: 3, y: 3});
    }
    {
        let person = Human;
        person.fly();
        Pilot::fly(&person);
        Wizard::fly(&person);
    }
    {
        println!("A baby dog is called a {}", Dog::baby_name());
    }
    {
        println!("A baby dog is called a {}", <Dog as Animal>::baby_name());
    }
    {
       

        trait OutlinePrint: fmt::Display {
            fn outline_print(&self) {
                let output = self.to_string();
                let len = output.len();
                println!("{}", "*".repeat(len + 4));
                println!("*{}*", " ".repeat(len + 2));
                println!("* {} *", output);
                println!("*{}*", " ".repeat(len + 2));
                println!("{}", "*".repeat(len + 4));
            }
        }
    }
    {
        struct Wrapper(Vec<String>);

        impl fmt::Display for Wrapper {
            fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
                write!(f, "[{}]", self.0.join(", "))
            }
        }
        let w = Wrapper(vec![String::from("hello"), String::from("world")]);
        println!("w = {}", w);
    }
    {
        fn add_one(x:i32) -> i32 {
            x + 1
        }
        fn do_twice(f: fn(i32) -> i32, arg: i32) -> i32 {
            f(arg) + f(arg)
        }
        let answer = do_twice(add_one, 5);
        println!("The answer is: {}", answer);
    }
    {
        let list_of_numbers = vec![1, 2, 3];
        let list_of_strings: Vec<String> = list_of_numbers.iter().map(|i| i.to_string()).collect();
        println!("{:?}", list_of_strings);

        let list_of_numbers = vec![1, 2, 3];
        let list_of_strings: Vec<String> = list_of_numbers.iter().map(ToString::to_string).collect();
        println!("{:?}", list_of_strings);
    }
    {
        HelloMacro::hello_macro();
        Pancakes::hello_macro();
    }
}


struct Pancakes ;

impl HelloMacro for Pancakes {
    fn hello_macro() {
        println!("Hello, Macro! My name is Pancakes!");
    }
}



static HELLO_WORLD: &str = "Hello, world!";

static mut COUNTER: u32 = 0;

fn add_to_count(inc: u32) {
    unsafe {
        COUNTER += inc;
    }
}
#[derive(Debug,Copy,Clone,PartialEq)]
struct Point {
    x: i32,
    y: i32,
}
impl Add for Point {
    type Output = Point;

    fn add(self, other: Point) -> Point {
        Point {
            x: self.x + other.x,
            y: self.y + other.y,
        }
    }
    
}

trait Pilot {
    fn fly(&self);
}
trait Wizard {
    fn fly(&self);
}
struct Human;
impl Pilot for Human {
    fn fly(&self) {
        println!("This is your captain speaking.");
    }
}
impl Wizard for Human {
    fn fly(&self) {
        println!("Up!");
    }
}
impl Human {
    fn fly(&self) {
        println!("*waving arms furiously*");
    }
}

trait Animal {
    fn baby_name() -> String;
}
struct Dog;
impl Dog {
    fn baby_name() -> String {
        String::from("Spot")
    }
}
impl Animal for Dog {
    fn baby_name() -> String {
        String::from("puppy")
    }
}
