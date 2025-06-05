use std::{sync::{mpsc,Arc,Mutex},thread};

// Job 类型定义：可以在线程间安全传递和执行的任务
// - Box<dyn FnOnce()> 表示一个堆分配的闭包
// - Send 表示可以在线程间安全传递
// - 'static 表示闭包中的所有引用具有静态生命周期
type Job = Box<dyn FnOnce() + Send + 'static>;

// 线程池结构体
pub struct ThreadPool{
    workers: Vec<Worker>,    // 工作线程集合
    seeder: mpsc::Sender<Job>,  // 任务发送器
}

impl ThreadPool {
    // 创建指定数量的线程池
    pub fn new(n: usize) -> ThreadPool {
        assert!(n > 0);  // 确保线程数大于0
        
        // 预分配工作线程vector的容量
        let mut workers = Vec::with_capacity(n);
        
        // 创建通道，用于发送任务
        let (seeder, receiver) = mpsc::channel();
        
        // 将接收器包装在 Arc 和 Mutex 中
        // - Arc: 允许多个工作线程共享所有权
        // - Mutex: 确保同一时间只有一个线程可以接收任务
        let receiver = Arc::new(Mutex::new(receiver));
        
        // 创建n个工作线程
        for id in 0..n { 
            workers.push(Worker::new(id, Arc::clone(&receiver)));
        }
        
        ThreadPool { workers, seeder }
    }

    // 执行任务的方法
    // F: 必须是可以在线程间安全传递且没有引用的闭包
    pub fn execute<F>(&self, f: F)
    where
        F: FnOnce() + Send + 'static,
    {
        let job = Box::new(f);  // 将任务装箱
        self.seeder.send(job).unwrap();  // 发送任务到通道
    }
}

// 工作线程结构体
struct Worker {
    id: usize,  // 工作线程的唯一标识符
    thread: thread::JoinHandle<()>,  // 线程句柄
}

impl Worker {
    // 创建新的工作线程
    fn new(id: usize, receiver: Arc<Mutex<mpsc::Receiver<Job>>>) -> Worker {
        // 创建实际的工作线程
        let thread = thread::spawn(move || loop {
            // 获取互斥锁并接收任务
            let job = receiver.lock().unwrap().recv().unwrap();
            println!("Worker {id} got a job; executing.");
            job();  // 执行任务
        });
        
        Worker { id, thread }
    }
}