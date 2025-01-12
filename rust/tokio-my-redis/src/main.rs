use mini_redis::{client,Result};
#[tokio::main]
async fn main() -> Result<()> {
    let mut client = client::connect("127.0.0.1:6379").await?;
    // let resp = client.get("foo".into()).await?;
    // println!("GOT: {:?}", resp);
    let resp = client.set("foo".into(), "bar".into()).await?;
    println!("GOT: {:?}", resp);
    Ok(())
}