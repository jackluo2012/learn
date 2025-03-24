//  为什么要用闭包
//  闭包和函数有什么不同
#[derive(Debug)]
struct User {
    name: String,
    score: u64,
}
//给用户排序
fn sort_users_by_score(users: &mut [User]) {
    users.sort_by_key(sort_helper);
}
// 不用闭包
fn sort_helper(u: &User)->u64 {
    u.score
}
// 用闭包
fn sort_score_closure(users: &mut [User]) {
    users.sort_by_key(|u| u.score);
}

fn main() {
    
    {
        let mut users = vec![
        User {
            name: String::from("Alice"),
            score: 30,
        },
        User {
            name: String::from("Bob"),
            score: 20,
        },
    ];
    sort_users_by_score(&mut users);
    println!("{:?}", users);
    sort_score_closure(&mut users);
    println!("{:?}", users);
    }
    {
        // fn 不可变引用 获取外部参数
        let s1 = String::from("11111111111111111");   
        let _s2 = String::from("22222222222222222");
        //不可变的fn
        let fn_func = |s| {
            println!("{s1}");
            println!("I am {s}");
            println!("{s1}");
        };
        fn_func("yz".to_owned());
        fn_func("原子".to_owned());
        println!("{s1} {_s2}");

        // fnMut 可变引用 获取外部参数
        // 拿走了所有权
        let s1 = String::from("11111111111111111");
        let mut fn_func = |mut s: String| {
            s.push_str("33333333333333333");
            println!("{s1}");
        };
        // 所有权转移 由编译器根据我们的代码来推断
        // fn_func(s1);
        // println!("{s1} {s2}");
        // 所有权转移 由编译器根据我们的代码来推断
        let s1  = String::from("11111111111111111");
        let fn_Once_func = |s: String| {            
            println!("I am {s}");
            println!("{s1}");
            
        };
        fn_Once_func(s1.clone());
        // println!("{s1}");
    }
    {
        let s1 = String::from("11111111111111111");
        let move_fn = move |s:String| {
            // println!("{s1}");
            println!("I am {s}");
            // println!("{s1}");
        };
        move_fn(s1);
        // println!("{s1}");
    }
}
