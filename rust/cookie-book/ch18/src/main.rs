use gui::{Button,Screen};
use blog::Post;
fn main() {
    {
        let screen = Screen {
            components: vec![
                Box::new(Button {
                    width: 5,
                    height: 10,
                    label: String::from("OK"),
                }),
                Box::new(SelectBox {
                    width: 75,
                    height: 10,
                    options: vec![
                        String::from("Yes"),
                        String::from("Maybe"),
                    ]
                })
                
            ],
        };
        screen.run();
    }
    {
        let mut post = Post::new();

        post.add_text("I ate a salad for lunch today");
        assert_eq!(post.content(), "");

        post.request_review();
        assert_eq!(post.content(),"");

        post.approve();
        assert_eq!(post.content(), "I ate a salad for lunch today");
    }
}
use gui::Draw;

struct SelectBox {
    width: u32,
    height: u32,
    options: Vec<String>,
}

impl Draw for SelectBox {
    fn draw(&self) {
        // code to actually draw a select box
    }
}
