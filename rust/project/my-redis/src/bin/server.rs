use tokio::net::{TcpListener, TcpStream};
use mini_redis::{Connection, Frame};
use bytes::Bytes;
use std::sync::{Arc, Mutex};
use mini_redis::Command::{self, Get, Set};
    use  std::collections::HashMap;
type Db = Arc<Mutex<HashMap<String, Bytes>>>;




#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    //监听指定地址，等待TCP进来
    let listener = TcpListener::bind("127.0.0.1:6379").await?;

    println!("Listening");

    let db = Arc::new(Mutex::new(HashMap::new()));

    loop {
        // 第二个被忽略的项中包含有新连接的 `IP` 和端口信息
        let (socket, _) = listener.accept().await?;
        // 将 handle 克隆一份
        let db = db.clone();
        // 为每一条连接都生成一个新的任务，
        // `socket` 的所有权将被移动到新的任务中，并在那里进行处理
        println!("Accepted");
        tokio::spawn(async move {
            process(socket,db).await;
        });
    }
}

async fn process(socket: TcpStream, db: Db) {
    
        
    // // `Connection` 对于 redis 的读写进行了抽象封装，
    // 因此我们读到的是一个一个数据帧frame(数据帧 = redis命令 + 数据)，
    // 而不是字节流
    // 创建一个 `Connection`，它实现了 `AsyncRead` 和 `AsyncWrite`。
     // `mini-redis` 提供的便利函数，使用返回的 `connection` 可以用于从 socket 中读取数据并解析为数据帧
    let mut connection = Connection::new(socket);
    // 使用 `read_frame` 方法从连接获取一个数据帧：一条redis命令 + 相应的数据
    while let Some(frame) = connection.read_frame().await.unwrap() {
        println!("GOT {:?}", frame);
        let response = match Command::from_frame(frame).unwrap() {
            Set(cmd) => {
                // 值被存储为`Vec<u8>` 的形式
                let mut db = db.lock().unwrap();
                db.insert(cmd.key().to_string(), cmd.value().clone());
                Frame::Simple("OK".to_string())
            }
            Get(cmd) => {
                let db = db.lock().unwrap();
                if let Some(value) = db.get(cmd.key()) {
                    // `Frame::Bulk` 的值被存储为 `Vec<u8>` 的形式
                    Frame::Bulk(value.clone().into())
                } else {
                    Frame::Null
                }

            }
            cmd => panic!("unimplemented {:?}", cmd),
        };
        // 将请求响应返回给客户端
        connection.write_frame(&response).await.unwrap();
        
    }
}