### tokio my-redis 学习
安装 miniredis
```shell
cargo install mini-redis #安装服务 
mini-redis-server # 启动服务
```
```shell
mini-redis-cli get foo #获取设置的值
```