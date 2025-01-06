use std::{
    thread,    
    sync::{mpsc, Mutex,Arc},
};
pub struct threadPool{
    workers: Vec<Worker>,
    sender: Option<mpsc::Sender<Job>>,
}
type Job = Box<dyn FnOnce() + Send + 'static>;

impl threadPool {
    pub fn new(size: usize) -> Self {
        assert!(size > 0);
        // 接收者 sender 和发送者 receiver 的通道   
        let (sender, receiver) = mpsc::channel();
        // 将 receiver 包装成 Arc<Mutex<T>> 类型
        let receiver = Arc::new(Mutex::new(receiver));
        // 创建线程池
        let mut works= Vec::with_capacity(size);
        // 创建工作线程
        for id in 0..size {
            // 将 receiver 的 Arc<Mutex<T>> 类型转换为 Arc<Mutex<T>> 类型            
            works.push(Worker::new(id,Arc::clone(&receiver)));
        }
        // 返回线程池
        threadPool{workers: works, sender: Some(sender)}
    }

    pub fn execute<F>(&self, f: F)
    where
        F: FnOnce() + Send + 'static,
    {
        // TODO
        let job = Box::new(f);
        self.sender.as_ref().unwrap().send(job).unwrap();
    }
}
impl Drop for threadPool {
    fn drop(&mut self) {
        drop(self.sender.take());
        for worker in &mut self.workers {
            println!("Shutting down worker {}", worker.id);

            if let Some(thread) = worker.thread.take() {
                println!("Shutting down worker {}", worker.id);
                thread.join().unwrap();
            }
        }
    }
}

struct Worker {
    id: usize,
    thread: Option<thread::JoinHandle<()>>,
}

impl Worker {
    fn new(id: usize,receiver: Arc<Mutex<mpsc::Receiver<Job>>>) -> Worker {
        let thread = thread::spawn(move || loop{
            let message = receiver.lock().unwrap().recv();
            // 接收任务
            match message {
                Ok(job) =>{
                    println!("Worker {} got a job; executing.", id);
                    job();
                }
                Err(_) =>{
                    println!("Worker {id} disconnected; shutting down.");
                    break;
                }
            }
        });
        Worker { 
            id, 
            thread:Some(thread) 
        }
    }
}
// impl Drop for threadPool {
//     fn drop(&mut self) {
//         for worker in &mut self.workers {
//             if let Some(thread) = worker.thread.take() {
//                 println!("Shutting down worker {}", worker.id);
//                 thread.join().unwrap();
//             }
//         }
//     }
// }
