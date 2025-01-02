use trpl::{Either,Html};
use std::future::Future;
use std::time::Duration;
use std::pin::Pin;  // 添加 Pin 的导入
use std::thread;
use std::time::Instant;
use trpl::{ReceiverStream, Stream, StreamExt};
fn main () {
    {
        trpl::run(async {

        });
    }
    {
        trpl::run(async {
            let values = [1,2,3,4,5,6,7,8,9,10];
            let iter = values.iter().map(|n| n*2);
            let mut stream = trpl::stream_from_iter(iter);
            while let Some(value) = stream.next().await {
                println!("The value was: {}", value);
            }
        });
    }
    {
        trpl::run(async {
            let values = 1..101;
            let iter = values.map(|n| n*2);
            let stream = trpl::stream_from_iter(iter);

            let mut filtered = stream.filter(|n| n % 3 == 0 || n % 5 == 0);

            while let Some(value) = filtered.next().await {
                println!("The value was: {}", value);
            }
        });
    }
    {
        trpl::run(async {
            let mut stream = get_message();
            while let Some(message) = stream.next().await {
                println!("{message}");
            }
        });
    }
}
fn get_message() -> impl Stream<Item = String> {
    let (tx, rx) = trpl::channel();
    let messages = ["a","b","c","d","e","f","g","h","i","j","k"];

    for message in messages {
        tx.send(format!("Message: '{message}'")).unwrap();        
    }
    ReceiverStream::new(rx)
}