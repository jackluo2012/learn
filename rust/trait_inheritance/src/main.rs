use std::collections::VecDeque;

// 多态
trait Driver {
    fn drive(&self);
}
#[derive(Debug)]
struct Car;
impl Driver for Car {
    fn drive(&self) {
        println!("Car is driving");
    }
}
#[derive(Debug)]
struct SUV;
impl Driver for SUV {
    fn drive(&self) {
        println!("SUV is driving");
    }
}
//展示特质的方法
//// 定义一个名为 road 的函数，
/// 接受一个实现了 Driver 特质的动态引用 vehicle
fn road(vehicle: &dyn Driver) {
    vehicle.drive();
}
//继承思想
// 单向特质
trait Queue {
    // 获取队列的长度
    fn len(&self) -> usize;
    // 向队列的尾部添加一个元素
    fn push_back(&mut self, item: i32);
    // 从队列的头部移除一个元素
    // 为了使代码更具体有可移动性，表达性，我们返回一个 Option<i32>，而不是 i32
    fn pop_front(&mut self) -> Option<i32>;
}
// 双向特质
// 可以实现上面的 Queue 特质，但是需要实现 pop_front 方法
// 有5个
trait Deque: Queue {
    // 从前面加入
    fn push_front(&mut self, item: i32);
    // 从前面移除
    fn pop_back(&mut self) -> Option<i32>;
}
//声明一个结构 实现上面的特质
#[derive(Debug)]
struct List {
    elements: VecDeque<i32>,
}
impl List {
    fn new() -> Self {
        List {
            elements: VecDeque::<i32>::new(),
        }
    }
}
impl Queue for List {
    fn len(&self) -> usize {
        self.elements.len()
    }
    fn push_back(&mut self, item: i32) {
        self.elements.push_back(item);
    }
    fn pop_front(&mut self) -> Option<i32> {
        self.elements.pop_front()
    }
}
impl Deque for List {
    fn push_front(&mut self, item: i32) {
        self.elements.push_front(item);
    }
    fn pop_back(&mut self) -> Option<i32> {
        self.elements.pop_back()
    }
}

fn main() {
    let car = Car;
    let suv = SUV;
    road(&car);
    road(&suv);
    println!("{:?}",car);
    println!("{:?}",suv);

    let mut list = List { elements: VecDeque::new() };
    list.push_back(1);
    list.push_back(2);
    list.push_back(3);
    println!("{:?}", list);
    list.push_front(0);
    println!("{:?}", list);
    list.pop_back();
    println!("{:?}", list);
    list.pop_front();
    println!("{:?}", list);
    list.pop_front();
    println!("{:?}", list);
    list.pop_front().unwrap();
}
