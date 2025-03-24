use crate::List::{Cons, Nil};
use std::ops::Deref;
use std::rc::Rc;

struct MyBox<T>(T);
impl<T> MyBox<T> {
    fn new(x: T) -> MyBox<T> {
        MyBox(x)
    }
}
impl <T> Deref for MyBox<T> {
    //语法定义了用于此 trait 的关联类型
    type Target = T;
    fn deref(&self) -> &T {
        &self.0
    }
}
fn hello(name: &str) {
    println!("Hello, {name}!");
}

struct CustomSmartPointer{
    data: String,
}
impl Drop for CustomSmartPointer {
    fn drop(&mut self) {
        println!("Dropping CustomSmartPointer with data `{}`!", self.data);
    }
}
fn main(){
    {
        let c = CustomSmartPointer { data: String::from("my stuff") };
        drop(c);
        let d = CustomSmartPointer { data: String::from("other stuff") };
        println!("CustomSmartPointer created.");
    }
    {
        let m = MyBox::new(String::from("Rust"));
        hello(&m);
        
    }
    {
        let b = Box::new(5);
        println!("Hello, world! {}", b);
    }
    {
        let list = Cons(1, Box::new(Cons(2, Box::new(Cons(3, Box::new(Nil))))));
        // let list = Cons(1, Cons(2, Cons(3, Nil)));
    }
    {
        let x = 5;
        let y = &x;
        // *y = *(y.deref()) ;
        assert_eq!(5, *y);
        assert_eq!(5, x);
    }
    {
        let x = 5;
        let y = Box::new(x);
        assert_eq!(5, *y);
        assert_eq!(5, x);
    }
    {
        let w = MyBox::new(5);
        assert_eq!(5, *w);
    }
    {
        let a = Cons(5, Box::new(Cons(10, Box::new(Nil))));
        let b = Cons(3, Box::new(a));
        let c = Cons(4, Box::new(b));
        // println!("{:?}", c);
    }
    {
        enum List{
            Cons(i32, Rc<List>),
            Nil,
        }
        let a = Rc::new(List::Cons(5, Rc::new(List::Cons(10, Rc::new(List::Nil)))));
        println!("count after creating a = {}",Rc::strong_count(&a));
        let b = List::Cons(3, Rc::clone(&a));
        println!("count after creating b = {}",Rc::strong_count(&a));
        {
            let c = List::Cons(4, Rc::clone(&a));
            println!("count after creating c = {}",Rc::strong_count(&a));
        }
        // let c = List::Cons(4, Rc::clone(&a));
        println!("count after creating c = {}",Rc::strong_count(&a));
    }
    
}
use std::cell::RefCell;

enum List {
    Cons(i32, Box<List>),
    // Cons(i32, List),
    Nil,
}

enum Message {
    Quit,
    Move { x: i32, y: i32 },
    Write(String),
    ChangeColor(i32, i32, i32),
}


