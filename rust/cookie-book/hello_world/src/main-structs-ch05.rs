fn main(){
    let width1= 30;
    let height1 = 50;
    println!("The area of the rectangle is {} square pixels.", area(width1, height1));

    let rect1 = (30,50);
    println!("The area of the rectangle is {} square pixels.", area2(rect1));
    let rect2 = Rectangle {
        width: 30,
        height: 50,
    };
    println!("The area of the rectangle is {} square pixels.", area3(rect2));
    let rect3 = Rectangle {
        width: 30,
        height: 50,
    };
    println!(" rectangle is {rect3:#?}");

    let scale = 2;
    let rect1 = Rectangle {
        width: dbg!(30 * scale),
        height: 50,
    };
    dbg!(&rect1);
    println!("The area of the rectangle is {} square pixels.", rect1.area());
    let rect4 = Rectangle {
        width: 30,
        height: 50,
    };
    if rect4.width() {
        println!("The rectangle has a nonzero width; it is {}.", rect4.width);
    }

    let rect5 = Rectangle {
        width: 30,
        height: 50,
    };
    let rect6 = Rectangle {
        width: 10,
        height: 40,
    };
    let rect7 = Rectangle {
        width: 60,
        height: 45,
    };
    println!("can rect5 hold rect5? {}", rect5.can_hold(&rect6));
    println!("can rect5 hold rect7? {}", rect5.can_hold(&rect7));

    let square = Rectangle::square(3);
    println!("square is {square:#?}");
}
#[derive(Debug)]
struct Rectangle {
    width: u32,
    height: u32,
}
impl Rectangle {
    fn area(&self) -> u32 {
        self.width * self.height
    }
    fn can_hold(&self, other: &Rectangle) -> bool {
        self.width > other.width && self.height > other.height
    }
    fn width(&self) -> bool {
        self.width > 0
    }
    fn square(size: u32) -> Self {
        Self {
            width: size,
            height: size,
        }
    }
}

fn area3(rectangle: Rectangle) -> u32 {
    rectangle.width * rectangle.height
}
fn area2(dimensions: (u32, u32)) -> u32 {
    dimensions.0 * dimensions.1
}
fn area(width: u32, height: u32) -> u32 {
    width * height
}