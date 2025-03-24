use std::ops::Add;
// 编译时 打印特质
#[derive(Debug)]
struct Point<T> {
    x: T,
    y: T,
}
// # #[derive(Debug)]
// 相当 于实现了这个特质
// impl println for Point<T> {
//     fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
//         write!(f, "Point x: {}, y: {}", self.x, self.y)
//     }
// }
// 实现加法运算符
// T这样的类型 它可以执行相加的操作
impl<T> Add for Point<T>
where
    T: Add<Output = T>,
{
    type Output = Point<T>;
    //直接 借用 所有权
    fn add(self, other: Point<T>) -> Point<T> {
        Point {
            x: self.x + other.x,
            y: self.y + other.y,
        }
    }
}
fn main() {
    let p1 = Point { x: 1, y: 2 };
    let p2 = Point { x: 3, y: 4 };
    let p3 = p1 + p2;
    println!("{:?}", p3);
    
}
