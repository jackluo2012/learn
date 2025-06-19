use anyhow::Result;
use s2n_quic::{client::Connect,Client};
use std::{error::Error, net::SocketAddr};
use tokio::io;
const CERTIFICATE: &str = include_str!("../fixtures/cert.pem");
#[tokio::main]
async fn main() -> Result<()> {
    let client = Client::builder()
        .with_tls(CERTIFICATE)?
        .with_io("0.0.0.0:0")?// 任意的port
        .start()?;
    
    println!("Client started, connecting to server...");
    let addr: SocketAddr = "127.0.0.1:4433".parse()?;
    let connect = Connect::new(addr).with_server_name("localhost");
    let mut connection = client.connect(connect).await?;

    // ensure the connection doesn't time out with inactivity
    connection.keep_alive(true)?;

    // open a new stream and split the receiving and sending sides
    let stream = connection.open_bidirectional_stream().await?;
    let (mut receive_stream, mut send_stream) = stream.split();

    // spawn a task that copies responses from the server to stdout
    tokio::spawn(async move {
        let mut stdout = io::stdout();
        if let Err(e) = io::copy(&mut receive_stream, &mut stdout).await {
            println!("Error copying from receive stream to stdout: {}", e);
        }
    });

    // copy data from stdin and send it to the server
    let mut stdin = io::stdin();
    if let Err(e) = io::copy(&mut stdin, &mut send_stream).await {
        println!("Error copying from stdin to send stream: {}", e);
    }

    Ok(())
}