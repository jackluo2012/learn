trait Overview {
    fn overview(&self)-> String {
        "Course".to_string()
    }
}
trait Another {
    fn hell(&self){
        println!("welcome to hell");
    }
}
//声明 两个结构 实现 headline
struct Course {
    headline: String,
    author: String,
}
//实现 Course trait
impl Overview for Course {
}
struct AnotherCourse {
    headline: String,
    author: String,
}
//实现 Another trait
impl Another for AnotherCourse {
}
//调用方法
//第一种 impl 的写法
fn call_overview(course: &impl Overview) {
    println!("{}", course.overview());
}
//第二种 impl 的写法 用的是泛型
fn call_overview_generic<T: Overview>(course: &T) {
    println!("{}", course.overview());
}
// 不同类型
fn call_overview_another(course: &impl Overview, course2: &impl Overview) {
    println!("{}", course.overview());
    course.hell();
}
// 必须相同类型
fn call_overview_another_generic<T: Overview>(item: &T, course: &T) {
    println!("{}", course.overview());
    course.hell();
}
// 多绑定的
fn call_overview_another_generic2<T: Overview + Another>(item: &T, course: &T) {
    println!("{}", course.overview());
    course.hell();
}
// impl 多绑定
fn call_overview_another3(item: &impl Overview + Another, course: &impl Overview + Another) {
    println!("{}", course.overview());
    course.hell();
}
fn call_mul_bind_generic<T>(item: &T) 
where T : Overview + Another {
    println!("{}", item.overview());
    item.hell();
}

fn main() {
    let course = Course {
        headline: "Rust".to_string(),
        author: "zhangsan".to_string(),
    };
    let course2 = Course {
        headline: "Rust".to_string(),
        author: "zhangsan".to_string(),
    };
    let course3 = AnotherCourse {
        headline: "Rust".to_string(),
        author: "zhangsan".to_string(),
    }
    call_overview(&course);
    call_overview_generic(&course2);
    // 不同类型可以调用 
    call_overview_another(&course, &course3);
    // 相同类型不可以调用
    // call_overview_another_generic(&course, &course3);
}
