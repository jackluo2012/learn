fn swap<T: Clone>(x: &mut T, y: &mut T) {
    let temp = x.clone();
    *x = y.clone();
    *y = temp;
}
struct Point<A,B> {
    x: A,
    y: B,
}
impl<A: Clone, B: Clone> Point<A,B> {
    fn new(x: A, y: B) -> Self {
        Point { x, y }
    }
    fn swap(&mut self) {
        swap(&mut self.x, &mut self.y);
    }
}
fn main() {
    let mut a = 1;
    let mut b = 2;
    swap(&mut a, &mut b);
    println!("a: {}, b: {}", a, b);
    let mut p = Point::new(1, 2);
    p.swap();
    println!("p.x: {}, p.y: {}", p.x, p.y);
}
