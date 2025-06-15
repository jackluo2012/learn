
use tokio::sync::mpsc;
use mini_redis::client;
use tokio::sync::oneshot;
use bytes::Bytes;

/// 管理任务可以使用该发送端将命令执行的结果传回给发出命令的任务
type Responder<T> = oneshot::Sender<mini_redis::Result<T>>;
#[derive(Debug)]
enum Command {
    Get {
        key: String,
        resp: Responder<Option<Bytes>>,
    },
    Set { 
        key: String,
        value: Bytes,
        resp: Responder<()>,

    }
}

#[tokio::main]
async fn main() {
     // 创建一个新通道，缓冲队列长度是 32
    let (tx, mut rx) = mpsc::channel(32);
    // 由于有两个任务，因此我们需要两个发送者
    let tx2 = tx.clone();
    // 生成两个任务，一个用于获取 key，一个用于设置 key
    let t1 = tokio::spawn(async move {
        let (resp_tx, resp_rx) = oneshot::channel();
        let cmd = Command::Get {
            key: "hello".to_string(),
            resp: resp_tx,
        };
        // 发将命令发送到消息通道
        tx.send(cmd).await;
        // 等待结果
        let res = resp_rx.await;
        println!("Got = {:?}", res)
    });
    let t2 = tokio::spawn(async move {
        let (resp_tx, resp_rx) = oneshot::channel();
        let cmd = Command::Set {
                key: "foo".to_string(),
                value: "bar".into(),
                resp: resp_tx,
            };
        // 发送 SET 请求    
        tx2.send(cmd).await;

        // 等待回复
        let res = resp_rx.await;
        println!("GOT = {:?}", res);
    });
    // while let Some(msg) = rx.recv().await {
    //     println!("Got: {}", msg);
    // }
    // 当从消息通道接收到一个命令时，该管理任务会将此命令通过 redis 连接发送到服务器
    let manager = tokio::spawn(async move {
        //建立到redis服务器的连接
        let mut client = client::connect("127.0.0.1:6379").await.unwrap();

        // 开始接收消息
        while let Some(cmd) = rx.recv().await {            
            match cmd {
                Command::Get { key,resp } => {
                    let res = client.get(&key).await;                    
                    // 将数据发送回给任务
                    let _ = resp.send(res);
                    
                }
                Command::Set { key, value ,resp} => {
                    let res = client.set(&key, value).await;
                    let _ = resp.send(res);
                }
            }
        }
    });
    t1.await.unwrap();
    t2.await.unwrap();
    manager.await.unwrap();

}