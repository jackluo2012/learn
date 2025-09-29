## 列出所有的key
```shell
docker exec dev-etcd etcdctl get "" --prefix --keys-only
```