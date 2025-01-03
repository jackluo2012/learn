pub struct Post {
    state: Option<Box<dyn State>>,
    content: String,
}

impl Post {
    pub fn new() -> Post {
        Post {
            state: Some(Box::new(Draft {})),
            content: String::new(),
        }
    }

    pub fn add_text(&mut self, text: &str) {
        self.content.push_str(text);
    }
    
    //请求审核博文的功能
    pub fn request_review(&mut self) {
        // 获取了state值的所有权，将state的Some值移出
        // 调用 take 方法将 state 字段中的 Some 值取出并留下一个 None
        if let Some(s) = self.state.take() {
            //Draft 改为 PendingReview
            // 这样的代码直接更新状态值。这确保了当 Post 被转换为新状态后不能再使用老 state 值
            self.state = Some(s.request_review());
        }
    }
    // 审核博文的功能
    pub fn approve(&mut self) {
        if let Some(s) = self.state.take() {
            self.state = Some(s.approve());
        }
    }

    // 获取博文的内容
    pub fn content(&self) -> &str {
        // 需要 Option 中值的引用而不是获取其所有权
        // 因此使用了 as_ref 方法来获取 Option 中值的引用
        self.state.as_ref().unwrap().content(self)
    }
}
trait State {
    //这个语法意味着该方法只可在持有这个类型的 Box 上被调用
    fn request_review(self: Box<Self>) -> Box<dyn State>;
    // 审核博文的功能
    fn approve(self: Box<Self>) -> Box<dyn State>;
    // 获取博文的内容
    // content 方法的默认实现来返回一个空字符串 slice。
    // 这意味着无需为 Draft 和 PendingReview 结构体实现 content 了

    fn content<'a>(&self, post: &'a Post) -> &'a str{
        ""
    }
}
// 实现了Draft 的 State
struct Draft {}

impl State for Draft {
    // 装箱的 PendingReview 结构体的实例
    // 其用来代表博文处于等待审核状态
    fn request_review(self: Box<Self>) -> Box<dyn State> {

        Box::new(PendingReview {})
    }
    // Draft 的 approve 方法返回一个 Draft 实例的 Box，
    // 因为处于 Draft 状态的博文不能被审核
    fn approve(self: Box<Self>) -> Box<dyn State> {
        self
    }

}

struct PendingReview {}
// 实现了PendingReview 的 State
impl State for PendingReview {
    // 相反它返回自身，因为当我们请求审核一个已经处于 
    // PendingReview 状态的博文，它应该继续保持 PendingReview 状态。
    fn request_review(self: Box<Self>) -> Box<dyn State> {
        // 过它不进行任何状态转换
       self
    }
    // 审核博文的功能
    fn approve(self: Box<Self>) -> Box<dyn State> {
        // 审核通过后，博文的状态会从 PendingReview 转换为 Published
        Box::new(Published {})
    }
    
}
struct Published {}
// 实现了Published 的 State
impl State for Published {
    // 审核通过后，博文的状态会从 PendingReview 转换为 Published
    fn request_review(self: Box<Self>) -> Box<dyn State> {
        self
    }
    // 审核通过后，博文的状态会从 PendingReview 转换为 Published
    fn approve(self: Box<Self>) -> Box<dyn State> {
        self
    }
    // 获取博文的内容
    fn content<'a>(&self, post: &'a Post) -> &'a str {
        &post.content
    }
}