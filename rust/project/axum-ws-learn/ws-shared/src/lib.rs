use serde::{Deserialize, Serialize};
use std::time::SystemTime;
#[derive(Serialize, Deserialize, Debug,PartialEq)]
pub struct Msg {
    pub room: String,
    pub data: MsgData,
    pub username: String,
    pub timestamp: u64,
}
#[serde(rename_all = "snake_case")]
#[derive(Serialize, Deserialize, Debug,PartialEq)]
pub enum   MsgData {
    Join, // 加入
    Leave, // 离开
    Message(String),
}

// 把一个字符串，转换成msg 
impl TryFrom<&str> for Msg {
    type Error = serde_json::Error;
    fn try_from(value: &str) -> Result<Self, Self::Error> {
        Ok(serde_json::from_str(value)?)
    }
}

impl TryFrom<&Msg> for String {
    type Error = serde_json::Error;
    fn try_from(msg: &Msg) -> Result<Self, Self::Error> {
        Ok(serde_json::to_string(msg)?)
    }
    
}

impl Msg {
    // 创建一个新的msg
    pub fn new(room: String,  username: String,data: MsgData) -> Self {
        Msg {
            room,
            data,
            username,
            timestamp: SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs() as u64,
        }
    }
    // 创建 join msg
    pub fn join(room: &str, username: &str) -> Self {
        Msg::new(room.into(), username.into(), MsgData::Join)
    }
    // 创建 leave msg
    pub fn leave(room: &str, username: &str) -> Self {
        Msg::new(room.into(), username.into(), MsgData::Leave)
    }
    // 创建 message
    pub fn message(room: &str, username: &str, content: String) -> Self {
        Msg::new(room.into(), username.into(), MsgData::Message(content))
    }
}