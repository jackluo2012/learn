use std::vec;

use tokio::io;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener,TcpStream};

#[tokio::main]
async fn main() -> io::Result<()> {
    let socket = TcpStream::connect("127.0.0.1:6142").await?;
    let (mut rd, mut wr) = io::split(socket);
    
    // 创建异步任务，在后台 写入数据
    tokio::spawn(async move {
        wr.write_all(b"hello\r\n").await?;
        wr.write_all(b"world\r\n").await?;        
        wr.flush().await?;
        Ok::<_,io::Error>(())
    });
    let mut buf = vec![0; 128];
    
    loop {
        let n = rd.read(&mut buf).await?;
        if n == 0 {
            break;
        }

        println!("read {} bytes: {:?}", n, &buf[..n]);
    }
    Ok(())
}