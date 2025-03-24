fn applay_closure<F:Fn(i32,i32)->i32>(f: F,x: i32,y: i32) -> i32 {
   f(x,y)
}
//不可变引用 闭包
fn closure_fn<F>(f: F)
 where
    F: Fn()
{
    f();
    f();
}
// 可变引用闭包
fn closure_fn_mut<F>(mut f: F)
 where
    F: FnMut()
{
    f();
    f();
}
// fnOnce
fn closure_fn_once<F>(f: F)
 where
    F: FnOnce()
{
    f();
}


// 闭包类型FnOnce、FnMut和Fn做函数参数的实例
fn main() {
    {
        let x =5;
        let y = 10;
        let add_closure = |a,b| {
            println!("a: {}, b: {}",a,b);
            a+b
        };
        let result = applay_closure(add_closure,x,y);
        println!("result: {}",result);
    }
    {
        // fn 不可变引用 只能传一种 
        let s1 = String::from("hello");
        //整体 || println!("s1: {}",s1) 是个 fn
        closure_fn(|| println!("s1: {}",s1));
    }
    {
        // fn mut 可变引用 可以传多种
        let mut s2 = String::from("hello");
        closure_fn_mut(|| s2.push_str(" world"));
        println!("s2: {}",s2);
    }
    {
        let s1 = String::from("hello");
        closure_fn_once(|| println!("s1: {}",s1));
        let mut s2 = String::from("hello");
        closure_fn_once(|| s2.push_str(" world"));
        println!("s2: {}",s2);
        // fn once 闭包只能调用一次
        let s3 = String::from("hello");
        closure_fn_once(|| println!("s3: {}",s3));

        println!("s3: {}",s3);
    }
}
