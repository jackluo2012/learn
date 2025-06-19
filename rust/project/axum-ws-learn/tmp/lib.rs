mod msg;


use std::sync::Arc;

use axum::{
    extract::{ws::{Message, Utf8Bytes, WebSocket},WebSocketUpgrade}, http::header::WARNING, response::IntoResponse, Extension
};
// 这个比手写的hashmap更快,不用 RwLock
use dashmap::{DashMap,DashSet};
use futures::{SinkExt, StreamExt};
use tracing::{warn, error};
use serde::de;
// 所有客户端需要广播的消息
use tokio::sync::broadcast;
pub use msg::{
    Msg,
    MsgData,
};

// 设置一个容量
const CAPACITY: usize = 64;
// 这里的 Arc<Msg> 是为了在多线程中共享消息

//服务端有一个状态 -> 直接用 state 不行
#[derive(Debug,Clone)]
struct State {
    // 一个用户，有多个房间
    user_rooms: DashMap<String, DashSet<String>>,
    // 房间有多个用户
    room_users: DashMap<String, DashSet<String>>,

    // 广播通道,用arc 包装，避免多线程时的所有权问题
    // 这里的 Arc<Msg> 是为了在多线程中共享消息
    tx: broadcast::Sender<Arc<Msg>>,
}

// state 需要实现 Clone trait
#[derive(Debug,Clone,Default)]
// 这里的 Arc<State> 是为了在多线程中共享状态
pub struct ChatState (Arc<State>);
impl Default for State {
    fn default() -> Self {
        let (tx, _) = broadcast::channel(100);
        State {
            user_rooms: DashMap::default(),
            room_users: DashMap::default(),
            tx,
        }
    }
    
}

impl ChatState {
    fn new() -> Self {
        ChatState(Arc::new(State::default()))
    }
    //根据用户返回房间
    pub fn get_user_rooms(&self, username: &str) -> Vec<String> {
        // 获取用户的房间
        self.0.user_rooms
            .get(username)
            .map_or_else(Vec::new, |rooms| rooms.clone().into_iter().collect())
        
    }
    // 根据房间返回用户
    pub fn get_room_users(&self, room: &str) -> Vec<String> {
        // 获取房间的用户
        self.0.room_users
            .get(room)
            .map_or_else(Vec::new, |users| users.clone().into_iter().collect())
            .to_vec()
    }
}


pub async fn ws_handler(ws: WebSocketUpgrade, Extension(state): Extension<ChatState>) -> impl IntoResponse {

    // 这里的 state 是 Arc<ChatState>，需要解包
    //虽然callback 只有一个参数，但是我们可以通过闭包传给 handle_socket
    ws.on_upgrade(|socket| handle_socket(socket, state))
}
async fn handle_socket<S>(mut socket: S, state: ChatState)
where
    S: SinkExt<Message> + StreamExt<Item = Result<Message, axum::Error>> + Send + 'static,
{
    // 当一个连接进来的时候 ，我们就能subscribe 到 broadcast channel
    let mut rx = state.0.tx.subscribe();
    // 将 WebSocket 拆分为发送端和接收端，这样在异步代码中，就不会有所有权问题了
    let (mut sender, mut receiver) = socket.split();
    // 这里可以处理 socket 的消息
    // 这里需要 clone state
    let state1 = state.clone();
    
    let mut recv_task = tokio::spawn(async move {
        while let Some(Ok(msg)) = receiver.next().await {
            match msg {
                // 这里的 msg 是 WebSocket 的消息
                Message::Text(text) => {
                    handle_message(text.as_str().try_into().unwrap(), state1.clone()).await;
                    // // 将 text 转换为 Msg
                    // if let Ok(msg) = Msg::try_from(text.as_str()) {
                    //     // 发送到广播通道
                    //     let _ = state1.0.tx.send(Arc::new(msg));
                    // } else {
                    //     warn!("Failed to parse message: {}", text);
                    // }
                }
                Message::Close(_) => {
                    // 处理关闭连接
                    break;
                }
                _ => {}
                
            }
        }
    });
    // todo!("handle socket")
    // 这里是接收广播消息的部分
    let mut send_task = tokio::spawn(async move {
        while let Ok(msg) = rx.recv().await {
            // 这里的 msg 是 Arc<Msg>，需要序列化为 String
            let msg_str = match serde_json::to_string(msg.as_ref()) {
                Ok(s) => s,
                Err(e) => {
                    warn!("Failed to serialize message: {}", e);
                    continue;
                }
            };
            let msg: Utf8Bytes = msg_str.as_str().into();

            // 将消息发送到 WebSocket
            if let Err(e) = sender.send(Message::Text(msg)).await {
                warn!("Failed to send message:");
                break;
            }
        }
    });
    // 如果有错误，则取消任务
    tokio::select! {
        _v1 = &mut recv_task => send_task.abort(),
        _v2 = &mut send_task => recv_task.abort(),
    }
    
    println!("WebSocket connection closed");
    // 这里可以清理状态，比如从房间中移除用户等
    //假设有一个jack_user
    let username = "jack_user";
    for room in state.get_user_rooms(username) {
        // 发送离开房间的消息
        if let Err(e) = state.0.tx.send(Arc::new(Msg::leave(&room, username))) {
            warn!("Failed to send leave message: {}", e);
        }
        
        // 处理离开房间
        let msg = Msg::leave(&room, username);
        handle_message(msg, state.clone()).await;
    }
    // 这里可以清理状态，比如从房间中移除用户等
    

}

async fn handle_message(msg: Msg, state: ChatState) {    
    // 用 &ChatState 是合理的，因为 DashMap/DashSet 支持并发写入，
    // 只要不需要更换整个 state 实例，引用就够了。
    // 如果你要跨线程持有 state，可以 clone，但这里只是借用即可。
    let msg = match msg.data {
        MsgData::Join => {
            // 处理加入房间
            let username = msg.username.clone();
            let room = msg.room.clone();
            state.0.user_rooms.entry(username.clone())
                .or_insert_with(DashSet::new)
                .insert(room.clone());
            state.0.room_users.entry(room)
                .or_insert_with(DashSet::new)
                .insert(username);
            msg
        }
        MsgData::Leave => {
            // 处理离开房间
            if let Some(rooms) = state.0.user_rooms.get_mut(&msg.username) {
                rooms.remove(&msg.room);
                if rooms.is_empty() {
                    drop(rooms); // 释放锁
                    // 如果用户没有房间了，就从 user_rooms 中移除
                    state.0.user_rooms.remove(&msg.username);
                }
            }
            if let Some(users) = state.0.room_users.get_mut(&msg.room) {
                users.remove(&msg.username);
                if users.is_empty() {
                    drop(users); // 释放锁
                    // 如果房间没有用户了，就从 room_users 中移除
                    state.0.room_users.remove(&msg.room);
                }
            }
            msg
        }
        _ => msg,
    };

    // 广播消息
    let msg = Arc::new(msg);
    if let Err(e) = state.0.tx.send(msg.clone()) {
        println!("Failed to send message: {}", e);
        warn!("Failed to send message: {}", e);
    }
}


#[cfg(test)]
mod tests { 
    use super::*;
    use anyhow::Result;
    use fake_socket::*;
    #[tokio::test]
    async fn handle_socket_should_work() -> Result<(),anyhow::Error> {
        // 创建两个虚拟客户端和一个状态
        

        let (mut client, socket) = create_fake_connection();
        let state = ChatState::new();
        // 模拟一个 WebSocket 连接
        let state1 = state.clone();
        tokio::spawn(async move {
            handle_socket(socket, state1).await;
        });
        
        // 发送一个加入房间的消息
        let join_msg = Msg::join("test_room", "test_user");
        let join_msg_str = serde_json::to_string(&join_msg)?;
        client.send(Message::Text(join_msg_str.into()))?;


        // 接收消息
        if let Some(Message::Text(text)) = client.recv().await {
            let msg: Msg = serde_json::from_str(&text)?;            
            assert_eq!(msg.room, "test_room");
            assert_eq!(msg.username, "test_user");
        } else {
            panic!("Expected a join message");
        }


        Ok(())
    }

    #[tokio::test]
    async fn handle_socket_join_should_work() -> Result<(),anyhow::Error> {
        let (mut client1, mut client2, state) = prepare_connections().await.unwrap();
        warn!("准备连接完成");
        let join_msg = Msg::join("test_room", "jackluo");
        let join_msg_str = serde_json::to_string(&join_msg)?;
        client1.send(Message::Text(join_msg_str.into()))?;
        // 接收加入房间的消息
        // verify state
        verify(&mut client1, "test_room", "jackluo", MsgData::Join).await?;
        verify(&mut client1, "test_room", "rose", MsgData::Join).await?;

        // let leave_msg = Msg::leave("test_room", "jackluo");
        let leave_msg2 = Msg::new("test_room".into(), "jackluo".into(), MsgData::Leave);
        let leave_msg_str = serde_json::to_string(&leave_msg2)?;
        client1.send(Message::Text(leave_msg_str.into()))?;
        // 接收离开房间的消息
        assert!(client2.recv().await.is_some());
        // verify(&mut client2, "test_room", "jackluo", MsgData::Leave).await?;

        Ok(())
    }
    #[tokio::test]
    async fn handle_socket_leave_should_work2() -> Result<(),anyhow::Error> {
        let (mut client1, mut client2, state) = prepare_connections().await.unwrap();
        // 模拟一个加入房间的消息
        verify(&mut client1, "test_room", "jackluo", MsgData::Join).await?;
        verify(&mut client2, "test_room", "rose", MsgData::Join).await?;
        Ok(())
    }
    #[tokio::test]
    async fn handle_socket_leave_should_work() -> Result<(),anyhow::Error> {
        let (mut client1, mut client2, state) = prepare_connections().await.unwrap();
        // 模拟一个加入房间的消息
        verify(&mut client1, "test_room", "jackluo", MsgData::Join).await?;
        verify(&mut client2, "test_room", "rose", MsgData::Join).await?;

        // 模拟离开房间
        let leave_msg = Msg::leave("test_room", "jackluo");
        let leave_msg_str = serde_json::to_string(&leave_msg)?;
        client1.send(Message::Text(leave_msg_str.into()))?;

        // 接收离开房间的消息
        verify(&mut client2, "test_room", "jackluo", MsgData::Leave).await?;

        // verify state
        assert!(!state.get_user_rooms("jackluo").contains(&"test_room".to_string()));
        assert!(state.get_user_rooms("rose").contains(&"test_room".to_string()));
        
        Ok(())
    }
    async fn prepare_connections() -> Result<(FakeClient<Message>, FakeClient<Message>,ChatState)> {
        let (mut client1, socket1) = create_fake_connection();
        let (mut client2, socket2) = create_fake_connection();
        
        
        let state = ChatState::new();
        
        // 模拟两个 WebSocket 连接
        let state1 = state.clone();
        
        
        tokio::spawn(async move {
            handle_socket(socket1, state1).await;
        });
        
        let state2 = state.clone();
        tokio::spawn(async move {
            handle_socket(socket2, state2).await;
        });
        
        let msg1 = &Msg::join("test_room", "jackluo");
        client1.send(Message::Text(serde_json::to_string(msg1)?.into()))?;
        
        let msg2 = &Msg::join("test_room", "rose");
        client2.send(Message::Text(serde_json::to_string(msg2)?.into()))?;

        // 模拟一个加入房间的消息
        verify(&mut client1, "test_room", "jackluo", MsgData::Join).await;
        verify(&mut client2, "test_room", "rose", MsgData::Join).await;
        
        // 接收到加入房间的消息
        assert!(client1.recv().await.is_some());
        assert!(client2.recv().await.is_some());
        
        Ok((client1, client2, state))
    }

    async fn verify(client: &mut FakeClient<Message>, room: &str, username: &str, data: MsgData) -> Result<()> {
        
        if let Some(Message::Text(text)) = client.recv().await {
            let msg: Msg = serde_json::from_str(&text)?;
            assert_eq!(msg.room, room);
            assert_eq!(msg.username, username);
            assert_eq!(msg.data, data);
        }
        Ok::<_,anyhow::Error>(())
    }


}