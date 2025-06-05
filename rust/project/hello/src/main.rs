// 导入必要的模块
use std::{
    fs, // 文件系统操作
    io::{prelude::*, BufReader}, // 输入/输出相关
    net::{TcpListener, TcpStream}, // 网络编程相关
    thread, // 多线程相关
    time::{Duration}, // 时间相关
};
// 导入自定义的线程池模块
use hello::ThreadPool;

// 主函数
fn main() {
    // 绑定监听地址和端口
    let listener = TcpListener::bind("127.0.0.1:8080").unwrap();
    
    // 创建一个包含 4 个线程的线程池
    let pool = ThreadPool::new(4);
    
    for stream in listener.incoming().take(2) {
        let stream = stream.unwrap();
        // 加入多线程
        pool.execute(||  {
            handle_connection(stream);
        });
        
    }
    // 程序关闭提示
    println!("Shutting down.");
}

// 处理连接函数
fn handle_connection(mut stream: TcpStream) {
    // 创建一个缓冲区来存储客户端发送的数据
    let mut buffer = [0; 1024];
    // 从流中读取数据到缓冲区
    stream.read(&mut buffer).unwrap();
    // 定义 GET 请求的字节数组
    let get = b"GET / HTTP/1.1\r\n";
    // 定义 sleep 请求的字节数组
    let sleep = b"GET /sleep HTTP/1.1\r\n";
    
   
    // 根据请求类型选择不同的响应
    let (status_line, filename) = if buffer.starts_with(get) {
        // 如果是 GET 请求，返回 200 OK 和 hello.html
        ("HTTP/1.1 200 OK", "hello.html")
    } else if buffer.starts_with(sleep) {
        // 如果是 sleep 请求，休眠 5 秒，然后返回 200 OK 和 hello.html
        thread::sleep(Duration::from_secs(5));
        ("HTTP/1.1 200 OK", "hello.html")
    } else {
        // 否则返回 404 NOT FOUND 和 404.html
        ("HTTP/1.1 404 NOT FOUND", "404.html")
    };
    // 读取指定文件内容
    let contents = fs::read_to_string(filename).unwrap();
    let length = contents.len();

    // 构建 HTTP 响应
    let response =
        format!("{status_line}\r\nContent-Length: {length}\r\n\r\n\n{contents}");

    // 将响应写入流中
    stream.write_all(response.as_bytes()).unwrap();
    // 刷新流，确保数据发送出去
    stream.flush().unwrap();

}
