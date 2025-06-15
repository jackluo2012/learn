use tokio::fs::File;
use tokio::io::{self, AsyncReadExt};

#[tokio::main]
async fn main() -> io::Result<()> {
    {
        let mut f = File::open("foo.txt").await?;
        let mut buffer = [0; 10];

        // 由于 buffer 的长度限制，当次的 `read` 调用最多可以从文件中读取 10 个字节的数据
        let n = f.read(&mut buffer[..]).await?;

        println!("The bytes: {:?}", &buffer[..n]);       
    }
    {
        let mut f = File::open("foo.txt").await?;
        let mut buffer = Vec::new();

        // 读取整个文件的内容
        f.read_to_end(&mut buffer).await?;
        println!("The bytes: {:?}", buffer)    
    }
     Ok(())
}