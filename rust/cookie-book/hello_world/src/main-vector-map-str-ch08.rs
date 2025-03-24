fn main(){
    {
        let v: Vec<i32> = Vec::new();
        let v = vec![1,2,3];
    }
    {
        let mut v = Vec::new();
        v.push(5);
        v.push(6);
        v.push(7);
        v.push(8);
    }
    //读取
    {
        let v = vec![1,2,3,4,5];
        let third: &i32 = &v[2];
        println!("The third element is {}", third);

        let third: Option<&i32> = v.get(2);
        match(third){
            Some(third) => println!("The third element is {}", third),
            None => println!("There is no third element"),
        }
    }
    {
        let v = vec![1,2,3,4,5];
        // let does_not_exist = &v[100];
        let does_not_exist = v.get(100);
        println!("The value of does_not_exist is: {:?}", does_not_exist);
    }
    {
        let mut v = vec![1,2,3,4,5];
        let first = &v[0];
        // v.push(6);
        println!("The value of first is: {}", first);
    }
    {
        let v = vec![100,32,57];
        for i in &v{
            println!("{}", i);
        }
        println!("------------------");
        println!("The value of first is: {:?}", v);
    }
    {
        let mut v = vec![100,32,57];
        for i in &mut v{
            *i += 50;
        }
        println!("------------------");
        println!("The value of first is: {:?}", v);
    }
    {
        #[derive(Debug)]
        enum SpreadsheetCell{
            Int(i32),
            Float(f64),
            Text(String),
        }
        let row = vec![
            SpreadsheetCell::Int(3),
            SpreadsheetCell::Text(String::from("blue")),
            SpreadsheetCell::Float(10.12),
        ];
        println!("------------------");
        println!("The value of first is: {row:?}");
    }
    {
        let mut s = String::new();
        s.push_str("hello");
        s.push('l');
        println!("------------------");
        println!("The value of first is: {s:?}");
    }
    {
        let data = "initial contents";
        let s = data.to_string();
        println!("------------------");
        let s = "initial contents".to_string();
        println!("The value of first is: {s:?}");
    }
    {
        let s = String::from("initial contents");
    }
    {
        let hello = String::from("السلام عليكم");
        println!(" ------------------");
        println!("this is a test {}", hello);
        let hello = String::from("Dobrý den");
        println!(" ------------------");
        println!("this is a test {}", hello);
        let hello = String::from("Hello");
        println!(" ------------------");
        println!("this is a test {}", hello);
        let hello = String::from("שלום");
        println!(" ------------------");
        println!("this is a test {}", hello);
        let hello = String::from("नमस्ते");
        println!(" ------------------");
        println!("this is a test {}", hello);
        let hello = String::from("こんにちは");
        println!(" ------------------");
        println!("this is a test {}", hello);
        let hello = String::from("안녕하세요");
        println!(" ------------------");
        println!("this is a test {}", hello);
        let hello = String::from("你好");
        println!(" ------------------");
        println!("this is a test {}", hello);
        let hello = String::from("Olá");
        println!(" ------------------");
        println!("this is a test {}", hello);
        let hello = String::from("Здравствуйте");
        println!(" ------------------");
        println!("this is a test {}", hello);
        let hello = String::from("Hola");
        println!(" ------------------");
        println!("this is a test {}", hello);    
    }
    {
        let mut s = String::from("foo");
        s.push_str("bar");
        println!("------------------");
        println!("The value of first is: {s:?}");
    }
    {
        let mut s1 = String::from("lo");
        let s2 = "la";
        s1.push_str(s2);
        println!("------------------");
        println!("The value of first is: {s1:?}");
        println!("The value of second is: {s2:?}");
    }
    {
        let mut s = String::from("lo");
        s.push('l');
        println!("------------------");
        println!("The value of first is: {s:?}");
    }
    {
        let s1 = String::from("Hello, ");
        let s2 = String::from("world!");
        let s3 = s1 + &s2; // 注意 s1 被移动了，不能继续使用
        println!("------------------");
        println!("The value of first is: {s3:?}");
        println!("The value of second is: {s2:?}");
    }
    {
        let s1 = String::from("tic");
        let s2 = String::from("tac");
        let s3 = String::from("toe");

        let s = format!("{}-{}-{}", s1, s2, s3);
        println!("------------------");
        println!("The value of first is: {s:?}");
    }
    {
        let hello = "Здравствуйте";
        let s = &hello[0..4];
        println!("------------------");
        println!("The value of first is: {s:?}");

    }
    {
        for c in "Зд".chars() {
            println!("{c}");
        }        
    }
    {
        for b in "Зд".bytes() {
            println!("{b}");
        }
        
    }
    {
        use std::collections::HashMap;
        let mut scores = HashMap::new();
        scores.insert(String::from("Blue"), 10);
        scores.insert(String::from("Yellow"), 50);
        println!("------------------");
        println!("The value of first is: {scores:?}");
    }
    {
        use std::collections::HashMap;

        let mut scores = HashMap::new();
    
        scores.insert(String::from("Blue"), 10);
        scores.insert(String::from("Yellow"), 50);
    
        let team_name = String::from("Blue");
        //copied 方法来获取一个 Option<i32> 而不是 Option<&i32>，
        // 接着调用 unwrap_or 在 scores 中没有该键所对应的项时将其设置为零
        let score = scores.get(&team_name).copied().unwrap_or(0);
        println!("------------------");
        println!("The value of first is: {score:?}");
    }
    {
        use std::collections::HashMap;

        let mut scores = HashMap::new();

        scores.insert(String::from("Blue"), 10);
        scores.insert(String::from("Yellow"), 50);

        for (key, value) in &scores {
            println!("{}: {}", key, value);
        }
        println!("------------------");
        println!("The value of first is: {scores:?}");
    }
    {
        use std::collections::HashMap;

        let field_names = String::from("Favorite color Favorite animal");
        let field_values = String::from("Blue elephant");

        let mut map = HashMap::new();
        map.insert(&field_names, &field_values);

        println!("------------------");
        println!("The value of first is: {map:?}");
        println!("The value of second is: {field_names:?}");
        println!("The value of third is: {field_values:?}");
    }
    {
        use std::collections::HashMap;

        let mut scores = HashMap::new();

        scores.insert(String::from("Blue"), 10);
        scores.insert(String::from("Blue"), 50);
        println!("------------------");
        println!("The value of first is: {scores:?}");
    }
    {
        use std::collections::HashMap;

        let mut scores = HashMap::new();

        scores.insert(String::from("Blue"), 10);

        scores.entry(String::from("Yellow")).or_insert(50);
        scores.entry(String::from("Blue")).or_insert(50);

        println!("------------------");
        println!("The value of first is: {scores:?}");
    }
    {
        use std::collections::HashMap;
        let text = "hello world wonderful world";
        let mut map = HashMap::new();

        for word in text.split_whitespace() {
            let count = map.entry(word).or_insert(0);
            *count += 1;
        }
        println!("------------------");
        println!("The value of first is: {map:?}");
        // println!("The value of second is: {count:?}");
    }
}