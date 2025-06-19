use anyhow::Result;
use s2n_quic::Server;
use std::{error::Error, path::Path};

const CERTIFICATE: &str = include_str!("../fixtures/cert.pem");
const KEY: &str = include_str!("../fixtures/key.pem");

#[tokio::main]
async fn main() -> Result<()> {
    let addr = "127.0.0.1:4433";
    let mut server = Server::builder()
        .with_tls((CERTIFICATE, KEY))?
        .with_io(addr)?
        .start()?;

    println!("Server listening on {}", addr);
    while let Some(mut connection) = server.accept().await {
        println!("Accepted connection from {}", connection.remote_addr()?);
        // spawn a new task for the connection
        tokio::spawn(async move {
            while let Ok(Some(mut stream)) = connection.accept_bidirectional_stream().await {
                println!("Accepted stream from {}", stream.connection().remote_addr().unwrap());
                
                // spawn a new task for the stream
                tokio::spawn(async move {
                    // 收到数据，
                    // echo any data back to the stream
                    while let Ok(Some(data)) = stream.receive().await {
                        //再发送回去
                        stream.send(data).await.expect("stream should be open");
                    }
                });
            }
        });
    }

    Ok(())
}