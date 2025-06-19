use std::net::SocketAddr;

use axum::{extract::ws::{WebSocket, WebSocketUpgrade, Message}, response::IntoResponse, routing::get, Router,extract::Extension};
use ws_server::{ws_handler, ChatState};
#[tokio::main]
async fn main() {
    let addr = SocketAddr::from(([127, 0, 0, 1], 3000));
    println!("Listening on {}", addr);
    // 创建 axum application
    let app = axum::Router::new()
        .route("/", axum::routing::get(root))
        .route("/ws", axum::routing::get(ws_handler).layer(Extension(ChatState::default())));
    
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn root() -> &'static str {
    "Hello, World!"
}
