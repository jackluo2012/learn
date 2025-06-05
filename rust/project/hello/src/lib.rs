// 导入需要的标准库组件
// - mpsc: 多生产者单消费者通道，用于线程间通信
// - Arc: 原子引用计数，用于在线程间共享数据
// - Mutex: 互斥锁，确保数据的互斥访问
// - thread: 线程管理模块
use std::{sync::{mpsc,Arc,Mutex},thread};

// Job 类型定义：可以在线程间安全传递和执行的任务
// - Box<dyn FnOnce()>: 将闭包装箱到堆上
// - Send: 保证类型可以安全地在线程间传递
// - 'static: 确保闭包中的引用具有静态生命周期
type Job = Box<dyn FnOnce() + Send + 'static>;

// 线程池结构体：管理一组工作线程
pub struct ThreadPool {
    workers: Vec<Worker>,    // 存储所有工作线程
    seeder: Option<mpsc::Sender<Job>>,  // 任务发送器，Option包装允许在析构时安全关闭
}

impl ThreadPool {
    // 创建新的线程池
    // n: 指定要创建的工作线程数量
    pub fn new(n: usize) -> ThreadPool {
        assert!(n > 0);  // 线程数必须大于0
        
        // 预分配存储工作线程的向量
        let mut workers = Vec::with_capacity(n);
        
        // 创建消息通道，用于向工作线程发送任务
        let (seeder, receiver) = mpsc::channel();
        
        // 包装接收端
        // - Arc使得多个工作线程可以共享接收端
        // - Mutex确保在同一时刻只有一个线程能接收任务
        let receiver = Arc::new(Mutex::new(receiver));
        
        // 创建指定数量的工作线程
        for id in 0..n { 
            workers.push(Worker::new(id, Arc::clone(&receiver)));
        }
        
        ThreadPool { workers, seeder: Some(seeder) }
    }

    // 向线程池提交任务
    // F: 符合 FnOnce + Send + 'static 约束的闭包类型
    pub fn execute<F>(&self, f: F)
    where
        F: FnOnce() + Send + 'static,
    {
        let job = Box::new(f);  // 将任务闭包装箱
        self.seeder.as_ref().unwrap().send(job).unwrap();  // 将任务发送给工作线程
    }
}

// 实现 Drop trait，用于线程池的清理工作
impl Drop for ThreadPool {
    fn drop(&mut self) {
        // 首先丢弃发送者，这会导致接收端收到错误，从而使工作线程退出
        drop(self.seeder.take());
        
        // 等待所有工作线程完成
        for worker in &mut self.workers {
            println!("Shutting down worker {}", worker.id);
            // 取出线程句柄并等待其结束
            if let Some(thread) = worker.thread.take() {
                thread.join().unwrap();
            } 
        }
    }       
}

// 工作线程结构体：表示线程池中的一个工作线程
struct Worker {
    id: usize,  // 工作线程的唯一标识符
    thread: Option<thread::JoinHandle<()>>,  // 线程句柄，Option允许在清理时取出所有权
}

impl Worker {
    // 创建新的工作线程
    // id: 工作线程标识符
    // receiver: 共享的任务接收器
    fn new(id: usize, receiver: Arc<Mutex<mpsc::Receiver<Job>>>) -> Worker {
        // 创建新线程并开始任务循环
        let thread = thread::spawn(move || loop {
            // 尝试接收任务
            let message = receiver.lock().unwrap().recv();
            
            match message {
                Ok(job) => {
                    println!("Worker {id} got a job; executing.");
                    job();  // 执行收到的任务
                }
                Err(_) => {
                    // 如果接收错误（通道已关闭），终止线程
                    println!("Worker {id} disconnected; shutting down.");
                    break;
                }
            }
        });
        
        Worker { id, thread: Some(thread) }
    }
}