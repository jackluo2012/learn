###
```shell
go mod init github.com/jackluo2012/learn/tree/main/go/etcd
```

### 监听变化
```shell
 go run watch.go
```
### 我们打开终端执行以下命令修改、删除、设置lmh这个key
```shell
etcdctl.exe --endpoints=http://127.0.0.1:2379 put lmh "lmh1"
etcdctl.exe --endpoints=http://127.0.0.1:2379 del lmh
etcdctl.exe --endpoints=http://127.0.0.1:2379 put lmh "lmh2"

```

