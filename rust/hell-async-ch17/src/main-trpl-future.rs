use trpl::{Either,Html};
use std::future::Future;
use std::time::Duration;
use std::pin::Pin;  // 添加 Pin 的导入
use std::thread;
use std::time::Instant;
fn page_title(url: &str) -> impl Future<Output = Option<String>> + '_ {
    async move {
        let response = trpl::get(url).await;
        let response_text = response.text().await;
        Html::parse(&response_text)
        .select_first("title")
        .map(|title_element| title_element.inner_html())
    }
}

async fn page_title_sync(url: &str) ->Option<String> {
    let response = trpl::get(url).await;
    let ressponse_text = response.text().await;
    Html::parse(&ressponse_text)
    .select_first("title")
    .map(|title_element| title_element.inner_html())
}

/**
 * cargo run https://www.baidu.com https://www.google.com 
 */
fn main() {  // 2. 将 main 函数标记为 async
    
    let args: Vec<String> = std::env::args().collect();
    {
        trpl::run(async {
            let url = &args[1];
            match page_title(url).await {
                Some(title) => println!("The title of {} is {}", url, title),
                None => println!("Failed to find the title of {}", url),
            }
        });
    }
    {
        let args: Vec<String> = std::env::args().collect();

        trpl::run(async {
            let title_fut_1 = page_title2(&args[1]);
            let title_fut_2 = page_title2(&args[2]);

            let (url, maybe_title) = match trpl::race(title_fut_1, title_fut_2).await {
                Either::Left(title) => title,
                Either::Right(title) => title,
            };
            println!("{url} returned first");
            match maybe_title {
                Some(title) => println!("The title of {} is {}", url, title),
                None => println!("Failed to find the title of {}", url),
            }
        })
    }
    {
        trpl::run(async {
            let handle = trpl::spawn_task(async {
                for i in 1..10 {
                    println!("hi number {i} from the first task!");
                    trpl::sleep(Duration::from_millis(500)).await;
                }
            });
            for i in 1..5 {
                println!("hi number {i} from the second task!");
                trpl::sleep(Duration::from_millis(500)).await;
            }
            handle.await.unwrap();
        });
    }
    {   
        trpl::run(async {
            let fut1 = async {
                for i in 1..10 {
                    println!("hixxxx number {i} from the first task!");
                    trpl::sleep(Duration::from_millis(500)).await;
                }
            };
            let fut2 = async {
                for i in 1..5 {
                    println!("hixxx number {i} from the second task!");
                    trpl::sleep(Duration::from_millis(500)).await;
                }
            };
    
            trpl::join(fut1,fut2).await;            
        })
    }
    {
        trpl::run(async {
            let (tx,mut rx) = trpl::channel();
            let val = String::from("hi");
            tx.send(val).unwrap();
            let received = rx.recv().await.unwrap();
            println!("Got: {received}");            
        })

    }
    {
        trpl::run(async {
            let (tx,mut rx) = trpl::channel();
            let vals = vec![
                String::from("hi"),
                String::from("from"),
                String::from("the"),
                String::from("future"),
            ];
            for val in vals {
                tx.send(val).unwrap();
                trpl::sleep(Duration::from_millis(500)).await;
            }
            // while let Some(received) = rx.recv().await {
            //     println!("Got: {received}");
            // }
        })
    }
    {
        trpl::run( async {
        let (tx,mut rx) = trpl::channel();
        // 发送消息的异步代码块只是借用了 tx，因为发送消息并不需要其所有权，
        // 但是如果我们可以将 tx 移动（move）进异步代码快，它会在代码块结束后立刻被丢弃
        let tx_fut = async move {
            let vals = vec![
                String::from("hi"),
                String::from("from"),
                String::from("the"),
                String::from("future"),
            ];
            for val in vals {
                tx.send(val).unwrap();
                trpl::sleep(Duration::from_millis(500)).await;
                
            }
        };
        let rx_fut = async {
            while let Some(received) = rx.recv().await {
                println!("Got: {received}");
            }
        };
        trpl::join(tx_fut,rx_fut).await;
        
        //     let (tx,rx) = trpl::channel();
        //     trpl::spawn(tx_fut);
        //     trpl::spawn(rx_fut);
        })
    }
    {
        trpl::run(async {
            let (tx,mut rx) = trpl::channel();
            let tx1 = tx.clone();
            let tx_fut = async move {
                let vals = vec![
                    String::from("hi"),
                    String::from("from"),
                    String::from("the"),
                    String::from("future"),
                ];
                for val in vals {
                    tx1.send(val).unwrap();
                    trpl::sleep(Duration::from_millis(500)).await;
                }
            };
            let rx_fut = async {
                while let Some(received) = rx.recv().await {
                    println!("received: '{received}'");
                }
            };
            let tx_fut2 = async move {
                let vals = vec![
                    String::from("more"),
                    String::from("messages"),
                    String::from("for"),
                    String::from("you"),
                ];
                for val in vals {
                    tx.send(val).unwrap();
                    trpl::sleep(Duration::from_millis(1500)).await;
                }
            };
            trpl::join!(tx_fut2,tx_fut,rx_fut);
        })
    }
    {
        trpl::run(async {
            let (tx,mut rx) = trpl::channel();
            let tx1 = tx.clone();
            let tx_fut = async move {
                let vals = vec![
                    String::from("hi"),
                    String::from("from"),
                    String::from("the"),
                    String::from("future"),
                ];
                for val in vals {
                    tx1.send(val).unwrap();
                    trpl::sleep(Duration::from_millis(500)).await;
                }
            };
            let rx_fut = async {
                while let Some(received) = rx.recv().await {
                    println!("received: '{received}'");
                }   
            };
            let tx_fut2 = async move {
                let vals = vec![
                    String::from("more"),
                    String::from("messages"),
                    String::from("for"),
                    String::from("you"),
                ];
                for val in vals {
                    tx.send(val).unwrap();
                    trpl::sleep(Duration::from_millis(1500)).await;
                }
            };
            let futures: Vec<Pin<Box<dyn Future<Output = ()>>>> = 
            vec![Box::pin(tx_fut),Box::pin(tx_fut2),Box::pin(rx_fut)];
            trpl::join_all(futures).await;
        })
    }
    {
        trpl::run(async {
            let a = async {
                1u32
            };
            let b = async {
                "hello！"
            };
            let c = async {
                true
            };
            let (a,b,c) = trpl::join3(a,b,c).await;
            println!("a:{a},b:{b},c:{c}");


        });
    }
    {
        trpl::run(async {
            let slow = async {
                println!("slow started");
                trpl::sleep(Duration::from_millis(100)).await;
                println!("slow finished");
            };
            let fast = async {
                println!("fast started");
                trpl::sleep(Duration::from_millis(50)).await;
                println!("fast finished");
            };
            trpl::race(slow,fast).await;
        });
    }
    {
        trpl::run(async {
            let a = async {
                println!("a started");
                slow("a",30);
                slow("a",10);
                slow("a",20);
                trpl::sleep(Duration::from_millis(50)).await;
                println!("a finished");
            };
            let b = async {
                println!("b started");
                slow("b",75);
                slow("b",10);
                slow("b",15);
                slow("b",350);
                trpl::sleep(Duration::from_millis(50)).await;
                println!("b finished");
            };
            trpl::race(a,b).await;
        });
    }
    {
        trpl::run(async {
            let one_ms = Duration::from_millis(1);

            let a = async {
                println!("'a' started.");
                slow("a", 30);
                trpl::sleep(one_ms).await;
                slow("a", 10);
                trpl::sleep(one_ms).await;
                slow("a", 20);
                trpl::sleep(one_ms).await;
                println!("'a' finished.");
            };
    
            let b = async {
                println!("'b' started.");
                slow("b", 75);
                trpl::sleep(one_ms).await;
                slow("b", 10);
                trpl::sleep(one_ms).await;
                slow("b", 15);
                trpl::sleep(one_ms).await;
                slow("b", 35);
                trpl::sleep(one_ms).await;
                println!("'b' finished.");
            };
    
        });
    }
    {
        trpl::run(async {
            let a = async {
                println!("'a' started.");
                slow("a", 30);
                trpl::yield_now().await;
                slow("a", 10);
                trpl::yield_now().await;
                slow("a", 20);
                trpl::yield_now().await;
                println!("'a' finished.");
            };
    
            let b = async {
                println!("'b' started.");
                slow("b", 75);
                trpl::yield_now().await;
                slow("b", 10);
                trpl::yield_now().await;
                slow("b", 15);
                trpl::yield_now().await;
                slow("b", 35);
                trpl::yield_now().await;
                println!("'b' finished.");
            };
     
        });
    }
    {
        trpl::run(async {
            let one_ns = Duration::from_nanos(1);
            let start = Instant::now();
            async {
                for _ in 1..1000 {
                    trpl::sleep(one_ns).await;
                }
            }
            .await;
            let time = Instant::now() - start;
            println!(
                "'sleep' version finished after {} seconds.",
                time.as_secs_f32()
            );
    
            let start = Instant::now();
            async {
                for _ in 1..1000 {
                    trpl::yield_now().await;
                }
            }
            .await;
            let time = Instant::now() - start;
            println!(
                "'yield' version finished after {} seconds.",
                time.as_secs_f32()
            );
    
        });
    }
    {
        trpl::run(async {
           let slow = async {
                trpl::sleep(Duration::from_secs(5)).await;
                "I finished!"
           };
           match timeout(slow, Duration::from_secs(2)).await {
               Ok(msg) => println!("Succeeded with '{msg}'"),
               Err(duration) => {
                println!("Failed after {} seconds", duration.as_secs())
               }
           }
        });
    }

}
async fn timeout<F: Future>(
    future_to_try: F,
    max_time: Duration,
) -> Result<F::Output, Duration> {
    match trpl::race(future_to_try, trpl::sleep(max_time)).await {
        Either::Left(output) => Ok(output),
        Either::Right(_) => Err(max_time),
    }
}
fn slow(name: &str,ms:u64) {
    thread::sleep(Duration::from_millis(ms));
    println!("'{name}' ran for {ms} ms");
}
async fn page_title2(url: &str) ->(&str,Option<String>) {
    let text = trpl::get(url).await.text().await;
    let title = Html::parse(&text).select_first("title").map(|title_element| title_element.inner_html());
    (url,title)
}