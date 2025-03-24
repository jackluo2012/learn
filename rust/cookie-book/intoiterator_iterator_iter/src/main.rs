
fn main() {
    // vec 可变数组
    let v = vec![1, 2, 3]; //实现了 intoterator trait 特质 into_iter
    //可变数组没有map,要转换成迭代器
    let v_iter = v.into_iter(); //move 所有权 
    let sum:i32 = v_iter.sum();
    println!("sum: {}", sum);
    
    let v1 = vec![1, 2, 3];
    let v1_iter = v1.iter(); //不可变借用
    println!("v1: {:?}",v1);
    // println!("v1: {:?}",v);
    
    

    // array 不可变数组
    let a = [1, 2, 3];
    let a_iter = a.iter(); //不可变借用
    println!("a: {:?}",a);
    let b = [1, 2, 3];
    let b_iter = b.into_iter(); //move 所有权
    println!("b: {:?}",b);
    // chars
    let s = String::from("hello");

    let s_iter = s.chars();
    let upper_s = s_iter.map(|c| c.to_uppercase().to_string()).collect::<String>();
    println!("upper_s: {}", upper_s);

   
    // range
}
