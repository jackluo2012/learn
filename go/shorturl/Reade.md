# 短链服务
```shell
mkdir -p shorturl/api
go mod init shorturl
```

###  API Gateway 代码

```shell
cd api
goctl api -o shorturl.api
goctl api go -api shorturl.api -dir .
```
- 下载依赖
```shell
go mod tidy
```
-　启动 API Gateway 服务
```shell
go run shorturl.go -f etc/shorturl-api.yaml
```

- 测试 API Gateway 服务
```shell
curl -i "http://localhost:8888/shorten?url=https://go-zero.dev"
```

- 在 shorturl 目录下创建 rpc/transform 目录
```shell
mkdir -p rpc/transform
```

- 在 rpc/transform 目录下编写 transform.proto 文件
```shell
goctl rpc -o transform.proto
```

- 用 goctl 生成 rpc 代码，在 rpc/transform 目录下执行命令
```shell
goctl rpc protoc transform.proto --go_out=. --go-grpc_out=. --zrpc_out=.
```

- 执行 go mod tidy 整理依赖
```shell
go mod tidy
```

- 启动 etcd server
```shell
go run transform.go -f etc/transform.yaml
```

- 列出所有的key
```shell
docker exec dev-etcd etcdctl get "" --prefix --keys-only
```
- 在 shorturl 目录下执行 go mod tidy 整理依赖

```shell
# etcd,redis,mysql 自行根据找教程安装启动
# 启动 rpc 服务
cd rpc/transform
go run transform.go -f etc/transform.yaml


cd api
go run shorturl.go -f etc/shorturl-api.yaml
```

- shorten api 调用
```shell
curl -i "http://localhost:8888/shorten?url=https://go-zero.dev"
```
- expand api 调用
```shell
curl -i "http://localhost:8888/expand?shorten=b0434f"
```
### Benchmark
```shell
docker run --rm -it williamyeh/wrk -t2 -c50 -d10s http://host.docker.internal:8888/expand?shorten=b688f2

```