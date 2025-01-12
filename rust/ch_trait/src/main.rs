trait Greeter {
    fn greet(&self);
    fn Hello(){
        println!("Hello, world!");
    } // fn Hello(&self);
}

struct Person {
    name: String,
}

impl Greeter for Person {
    fn greet(&self) {
        println!("Hello, {}!", self.name);
    }
    // fn Hello() {
    //     println!("Hello, world!");
    // }
}

fn main() {
    let person = Person {
        // name: String::from("Alice"),
        // name: "jackluo".to_owned(),
        name: "jackluo".to_string(),
    };
    person.greet();
    Person::Hello();
}
 