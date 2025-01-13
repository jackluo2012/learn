use std::fmt::Debug;
//Debug Clone Copy  PartialEq PartialEq
// 层级关系
// 有一个用户，我们统计一种族群，有不同种类的用户，有不同种类的用户行为
#[derive(Clone)]
enum Race {
    White, //白人
    Black,// 黑人
    Yellow,//黄种人
}
//要么实现这个
// #[derive(Debug)]
// 要么实现这个
impl Debug for Race {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Race::White => write!(f, "White"),
            Race::Black => write!(f, "Black"),
            Race::Yellow => write!(f, "Yellow"),
        }
    }
}
impl PartialEq for Race {
    fn eq(&self, other: &Self) -> bool {
        match (self, other) {
            (Race::White, Race::White) => true,
            (Race::Black, Race::Black) => true,
            (Race::Yellow, Race::Yellow) => true,
            _ => false,
        }
    }
}
// 用户
#[derive(Clone)]
struct User {
    id: u32,
    name: String,
    race: Race,
}
impl Debug for User {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("User")
            .field("id", &self.id)
            .field("name", &self.name)
            .field("race", &self.race)
            .finish()
    }
}
// 实现相等
impl PartialEq for User {
    fn eq(&self, other: &Self) -> bool {
        self.id == other.id && self.name == other.name && self.race == other.race
    }
}

fn main() {
    let user = User {
        id: 1,
        name: "test".to_string(),
        race: Race::White,
    };
    // {:?} debug打印结构体
    // 不能直接打印，要实现Debug
    println!("{:?}", user);
    let user2 = user.clone();
    println!("{:?}", user);
    println!("{:?}", user2==user);
}
