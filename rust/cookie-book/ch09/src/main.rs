// &【32】 引用 和用 Vec 没有问题
// Loop
fn sum_with_loop(list: &Vec<i32>) -> i32 {
    let mut sum = 0;
    for i in list {
        sum += i;
    }
    sum
}
// iterator
fn sum_with_iterator(list: &Vec<i32>) -> i32 {
    list.iter().sum()
}

fn main() {
    let list = vec![1, 2, 3, 4, 5];
    println!("{}", sum_with_loop(&list));
    println!("{}", sum_with_iterator(&list));
    
    const ARRAY_SIZE: usize = 10000;
    let array:Vec<i32> = (1..=ARRAY_SIZE as i32).collect();
    println!("{}", sum_with_iterator(&array));
    println!("{}", sum_with_loop(&array));
}
