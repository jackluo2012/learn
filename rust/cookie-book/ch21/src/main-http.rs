use std::{
    fs,
    net::{TcpListener,TcpStream},
    io::{prelude::*, BufReader},
    thread,
    time::Duration,
    
};

fn main() {
    let listener = TcpListener::bind("127.0.0.1:7878").unwrap();
    //获取到连接时打印信息
    for stream in listener.incoming() {
        let stream = stream.unwrap();
        // println!("Connection established")
        // handle connection (e.g. read request, process, send response)
        handle_connection(stream);
    }
}

fn handle_connection(mut stream: TcpStream) {
    //读取流中的数据
    let buf_reader = BufReader::new(&mut stream);
    //读取流中的数据，直到遇到空行
    // let http_request: Vec<_> = buf_reader
    //     //lines 方法通过遇到换行符（newline）字节就切分数据流的方式返回一个 迭代器
    //     .lines()
    //     //lines 返回的迭代器会生成 Result<String, std::io::Error> 类型的值
    //     .map(|result| result.unwrap())
    //     //take_while 方法会生成一个迭代器，这个迭代器会包含满足闭包中条件的所有元素，直到遇到第一个不满足条件的元素为止
    //     //这里就是遇到空行就停止
    //     .take_while(|line| !line.is_empty())
    //     //collect 方法将迭代器中的元素收集到一个集合中
    //     .collect();

    // let status_line = "HTTP/1.1 200 OK";
    // let contents = fs::read_to_string("hello.html").unwrap();
    
    // let response = format!("{status_line}\r\n\r\n{contents}");
    // stream.write_all(response.as_bytes()).unwrap();
    // println!("Request: {http_request:#?}");

    let request_line = buf_reader.lines().next().unwrap().unwrap();

    // if request_line == "GET / HTTP/1.1" {
    //     let status_line = "HTTP/1.1 200 OK";
    //     let contents = fs::read_to_string("hello.html").unwrap();

    //     let response = format!("{status_line}\r\n\r\n{contents}");
    //     stream.write_all(response.as_bytes()).unwrap();
    // }else{
    //     let status_line = "HTTP/1.1 404 NOT FOUND";
    //     let contents = fs::read_to_string("404.html").unwrap();
    //     let length = contents.len();
    //     let response = format!("{status_line}\r\nContent-Length: {length}\r\n\r\n{contents}");

    //     stream.write_all(response.as_bytes()).unwrap();
    // }
    // let (status_line, filename) = if request_line == "GET / HTTP/1.1" {
    //     ("HTTP/1.1 200 OK", "hello.html")
    // } else {
    //     ("HTTP/1.1 404 NOT FOUND", "404.html")
    // };
    // 我们需要显式匹配一个 slice 的 request_line 以匹配字符串字面值的模式，因为 request_line 是一个 &str，而不是一个 String。
    // match 不会像相等方法那样自动引用和解引用。
    let (status_line, filename) = match &request_line[..] {
        "GET / HTTP/1.1" => ("HTTP/1.1 200 OK", "hello.html"),
        "GET /sleep HTTP/1.1" => {
            thread::sleep(Duration::from_secs(5));
            ("HTTP/1.1 200 OK", "hello.html")
        }
        _ => ("HTTP/1.1 404 NOT FOUND", "404.html"),
    }

    let contents = fs::read_to_string(filename).unwrap();
    let length = contents.len();

    let response = format!("{status_line}\r\nContent-Length: {length}\r\n\r\n{contents}");
    stream.write_all(response.as_bytes()).unwrap();
}
