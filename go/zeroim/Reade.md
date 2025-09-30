### go-zero im 聊天室系统
```shell
mkdir zeroim && cd zeroim
go mod init zeroim
goctl api new imapi #初始化api服务
goctl rpc new imrpc #初始化rpc服务
```
- 初始化mq服务
```shell
mkdir immq && touch immq.go
```

- 初始化edge服务
```shell
goctl rpc new edge

go mod tidy
```
