#[derive(Debug)]
struct Stack<T> {
    items: Vec<T>,  
}
impl<T> Stack<T> {
    fn new() -> Self {
        Stack { items: Vec::new() }
    }
    //入栈
    fn push(&mut self, item: T) {
        self.items.push(item);
    }
    // 出栈
    fn pop(&mut self) -> Option<T> {
        self.items.pop()
    }
    // 不可变引用 迭代器
    fn iter(&self) -> std::slice::Iter<T> {
        self.items.iter()
        
    }
    // 可变引用 
    fn iter_mut(&mut self) -> std::slice::IterMut<T> {
        self.items.iter_mut()
    }
    // 所有权 转移
    fn into_iter(self) -> std::vec::IntoIter<T> {
        self.items.into_iter()
    }
}

fn main() {
    {
        let vec = vec![1, 2, 3, 4, 5];
        // iter（） 不可变引用 迭代器
        for i in vec.iter() {
            println!("{}", i);
        }
        println!("------------------");
        println!("vec: {:?}", vec);

        // iter_mut() 可变引用 迭代器
        let mut vec2 = vec![1, 2, 3, 4, 5];
        for i in vec2.iter_mut() {
            *i += 1;
        }
        println!("vec2: {:?}", vec2);

        //所有权 转移
        let vec3 = vec![1, 2, 3, 4, 5];
        let vec4 = vec3.into_iter().map(|x| x * 2).collect::<Vec<i32>>();
        println!("vec4: {:?}", vec4);
        // println!("vec3: {:?}", vec3);
    }
    {
        let mut stack = Stack::new();
        stack.push(1);
        stack.push(2);
        stack.push(3);
        for i in stack.iter() {
            println!("{}", i);
        }
        println!("------------------");
        println!("stack: {:?}", stack);
    }
    {
        let mut stack = Stack::new();
        stack.push(1);
        stack.push(2);
        stack.push(3);
        for i in stack.iter_mut() {
            *i += 1;
        }
        println!("stack: {:?}", stack);        
    }
    {
        let mut stack = Stack::new();
        stack.push(1);
        stack.push(2);
        stack.push(3);
        for i in stack.into_iter() {
            println!("{}", i);
        }
        println!("------------------");
        // println!("stack: {:?}", stack);
    }
}
