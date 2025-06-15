### Tokio my My-redis项目
### 需要在cargo.toml中添加依赖
```bash
cargo run --example hello-redis



cargo run --bin echo-server-copy


```




### 前期准备
#### 安装mini-redis.server 端 
```
cargo install mini-redis
```
#### 启动
```
mini-redis-server
```
#### 获取值 
```
mini-redis-cli get foo
```

#### 创建 项目
```
cargo new my-redis
cd my-redis
```
#### 命令
```
cargo run --bin server

cargo run --bin client
```