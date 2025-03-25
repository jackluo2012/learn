use mini_redis::{Connection, Frame};
use tokio::net::{TcpListener, TcpStream};
use std::collections::HashMap;
use bytes::Bytes;
use std::sync::{Arc, Mutex,MutexGuard};
type Db = Arc<Mutex<HashMap<String, Bytes>>>;
type SharedDb = Arc<Vec<Mutex<HashMap<String, Vec<u8>>>>>;

#[tokio::main]
async fn main() {
    let listener = TcpListener::bind("127.0.0.1:6379").await.unwrap();
    
    println!("Listening");

    let db = Arc::new(Mutex::new(HashMap::<String, Bytes>::new()));
    
    loop {
        let (socket, _) = listener.accept().await.unwrap();
        let db = db.clone();
        tokio::spawn(async move {
            
            process(socket,db).await;
        });
        

    }
}
async fn process(socket: TcpStream,db: Db) {
    use mini_redis::Command::{self,Get,Set};    

    let mut connection = Connection::new(socket);

    while let Some(frame) = connection.read_frame().await.unwrap() {
        let response = match Command::from_frame(frame).unwrap() {
            Set(cmd) => {
                let mut db = db.lock().unwrap();
                
                db.insert(cmd.key().to_string(), cmd.value().clone());
                Frame::Simple("OK".to_string())
            }
            Get(cmd) => {
                let db = db.lock().unwrap();

                
                if let Some(value) = db.get(cmd.key()) {
                    Frame::Bulk(value.clone())
                } else {
                    Frame::Null
                }
            }
            cmd => panic!("unimplemented {:?}", cmd),
        };

        connection.write_frame(&response).await.unwrap();

    }
}    
async fn increment_and_do_stuff(mutex: &Mutex<i32>) {
    {
        let mut lock: MutexGuard<i32> = mutex.lock().unwrap();
        *lock += 1;
    }
    do_something_async().await;
}

async fn do_something_async() {
    println!("Doing something async...");
}

struct CanIncrement {
    mutex:Mutex<i32>
}

impl CanIncrement {
    fn increment(&mut self){
        let mut lock = self.mutex.lock().unwrap();
        *lock += 1;
    }
}

async fn increment_and_do_stuff_2(can_increment: &mut CanIncrement) {
    can_increment.increment();
    do_something_async().await;
}

fn new_shared_db(num_shareds:usize) -> SharedDb {
    let mut db = Vec::new();
    for _ in 0..num_shareds {
        db.push(Mutex::new(HashMap::<String, Vec<u8>>::new()));
    }
    Arc::new(db)
}