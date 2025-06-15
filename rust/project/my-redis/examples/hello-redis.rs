use mini_redis::{client, Result};

#[tokio::main]
async fn main() -> Result<()> {
    // 建立 与mini-redis服务器的连接
    let mut client =client::connect("127.0.0.1:6379").await?;
    // 设置 key : "Hello" 和 value : "World"
    client.set("hello", "workd".into()).await?;

    // 获取 key : "Hello" 的值
    let result = client.get("hello").await?;
    println!("从服务器端获取到结果={:?}", result);

    Ok(())
}
