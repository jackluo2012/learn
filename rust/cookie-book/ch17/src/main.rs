use std::{pin::pin, time::Duration};
use trpl::{ReceiverStream, Stream, StreamExt};

enum Color {
    Rgb(i32, i32, i32),
    Hsv(i32, i32, i32),
}

enum Message {
    Quit,
    Move { x: i32, y: i32 },
    Write(String),
    ChangeColor(Color),
}
fn main() {
    {
        trpl::run(async {
            let values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
                let iter = values.iter().map(|n| n * 2);
                let mut stream = trpl::stream_from_iter(iter);

            while let Some(value) = stream.next().await {
                println!("The value was: {value}");
            }
        })
    }
    {
        trpl::run(async { 
            let mut messages = get_messages();
            while let Some(message) = messages.next().await {
                println!("{message}");
            }
        })
    }
    {
        trpl::run(async {
            let mut messages = pin!(get_messages2().timeout(Duration::from_millis(200)));

            while let Some(result) = messages.next().await {
                match result {
                    Ok(message) => println!("{message}"),
                    Err(reason) => eprintln!("Problem: {reason:?}"),
                }
            }
        })
    }
    {
        trpl::run(async {
            let messages = get_messages().timeout(Duration::from_millis(200));
        let intervals = get_intervals()
            .map(|count| format!("Interval: {count}"))
            .throttle(Duration::from_millis(100))
            .timeout(Duration::from_secs(10));
        let merged = messages.merge(intervals).take(20);
        let mut stream = pin!(merged);
        })
    }
    {
        let msg = Message::ChangeColor(Color::Hsv(0, 160, 255));

        match msg {
            Message::ChangeColor(Color::Rgb(r, g, b)) => {
                println!("Change color to red {r}, green {g}, and blue {b}");
            }
            Message::ChangeColor(Color::Hsv(h, s, v)) => {
                println!("Change color to hue {h}, saturation {s}, value {v}")
            }
            _ => (),
        }
    }
}
fn get_intervals()-> impl Stream<Item = u32> {
    let (tx,rx) = trpl::channel();

    trpl::spawn_task(async move {
        let mut count = 0;
        loop {
            trpl::sleep(Duration::from_millis(1)).await;
            
            count += 1;
            tx.send(count).unwrap();
        }
    });

    ReceiverStream::new(rx)
}
fn get_messages2() ->impl Stream<Item = String> {
    let (tx,rx) = trpl::channel();

    trpl::spawn_task(async move {
        let messages = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"];
        for (index, message) in messages.into_iter().enumerate() {
            let time_to_sleep = if index % 2 == 0 { 100 } else { 300 };
            trpl::sleep(Duration::from_millis(time_to_sleep)).await;

            tx.send(format!("Message: '{message}'")).unwrap();
        }
    });

    ReceiverStream::new(rx)


}
fn get_messages() -> impl Stream<Item = String> {
    let (tx,rx) = trpl::channel();

    let messages = ["a","b","c","d","e","f"];
    for message in messages {
        tx.send(format!("Message: '{message}'")).unwrap();
    }
    ReceiverStream::new(rx)

}

