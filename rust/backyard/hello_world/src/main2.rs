fn main() {
    

    

    //循环
    loop_test();
    while_test();
    for_test();
    for_test2();
    for_test3();
    //所有权
    string_own();
    test_ownership();
    test_ownership2();
    str_reference();
    test_refernece_change();
    test_refernece_change2();

    //结构体
    test_struct();
    test_struct2();
}
fn test_struct2() {
    let black = Color(0, 0, 0);
    let origin = Point(0, 0, 0);
}
struct User {
    username: String,
    email: String,
    sign_in_count: u64,
    active: bool,
}
struct Color(i32, i32, i32);
struct Point(i32, i32, i32);
fn test_struct() {
    

    let mut user1 = User {
        email: String::from("someone@example.com"),
        username: String::from("someusername123"),
        active: true,
        sign_in_count: 1,
    };
}
fn build_user(email: String, username: String) -> User {
    User {
        email,
        username,
        active: true,
        sign_in_count: 1,
    }
}


fn str_slice() {
    let my_string = String::from("hello world");
    let word = first_word(&my_string[0..6]);
    let word = first_word(&my_string[..]);

    let word = first_word(&my_string);

    let my_string_literal = "hello world";

    let word = first_word(&my_string_literal[0..6]);
    let word = first_word(&my_string_literal[..]);

    let word = first_word(my_string_literal);
}

fn first_word(s: &str) -> usize {
    let bytes = s.as_bytes(); // 将字符串转为字节数组

    for (i, &item) in bytes.iter().enumerate() {// iter() 方法返回一个迭代器，enumerate() 方法返回一个元组迭代器
        if item == b' ' {
            return i;
        }
    }
    s.len()
}
fn first_word2(s: &str) -> &str {
    let bytes = s.as_bytes();

    for (i, &item) in bytes.iter().enumerate() {
        if item == b' ' {
            return &s[0..i];
        }
    }
    &s[..]
}

fn test_refernece_change2(){
    let mut s = String::from("hello");

    let r1 = &s; // 没问题
    let r2 = &s; // 没问题
    println!("{r1} and {r2}");
    // 此位置之后 r1 和 r2 不再使用

    let r3 = &mut s; // 没问题
    println!("{r3}");
}
fn test_refernece_change(){
    let mut s = String::from("hello");
    change(&mut s);
}

fn change(some_string:&mut String){
    some_string.push_str(",world");
}

fn test_ownership2(){
    let s1 = String::from("hello");

    let (s2, len) = calculate_length2(s1);

    println!("The length of '{s2}' is {len}.");
}

fn str_reference(){
    let s1 = String::from("hello");
    let len = calculate_length(&s1);
    println!("The length of '{s1}' is {len}.");
}
fn calculate_length2(s: String) -> (String, usize) {
    let length = s.len(); // len() 返回字符串的长度

    (s, length)
}

fn calculate_length(s:&String) -> usize{
    s.len()
}


fn test_ownership(){
    let s1 = gives_ownership();
    let s2 = String::from("hello");
    let s3 = takes_and_gives_back(s2);
}


fn gives_ownership() -> String{
    let some_string = String::from("yours");
    some_string
}

fn takes_and_gives_back(a_string: String)-> String{
    a_string
}

fn string_own(){
    let mut s = String::from("hello");
    s.push_str(",world!");
    println!("{s}");

    takes_ownership(s);
    let x = 5;
    makes_copy(x);
}

fn takes_ownership(some_string:String){
    println!("{some_string}");
}

fn makes_copy(some_integer:i32){
    println!("{some_integer}");
}


// for range rev
fn for_test3(){
    for number in (1..4).rev() {
        println!("{number}!");
    }
    println!("LIFTOFF!!!");
}

// for in 
fn for_test2(){
    let a = [10, 20, 30, 40, 50];

    for element in a {
        println!("the value is: {element}");
    }
}

// for 测试
fn for_test(){
    let a = [10, 20, 30, 40, 50];
    let mut index = 0;

    while index < 5 {
        println!("the value is: {}", a[index]);

        index += 1;
    }
}

//while 测试
fn while_test(){
    let mut number = 3;

    while number != 0 {
        println!("{number}!");

        number -= 1;
    }

    println!("LIFTOFF!!!");
}

//** loop 测试
fn loop_test(){
    let mut count = 0;
    'counting_up: loop {
        println!("count = {count}");
        let mut remaining = 10;

        loop {
            println!("remaining = {remaining}");
            if remaining == 9 {
                break;
            }
            if count == 2 {
                break 'counting_up;
            }
            remaining -= 1;
        }

        count += 1;
    }
    println!("End count = {count}");
}