### 为container设置代理

#### 1. 在containerd中设置代理

```shell
sudo vi /etc/systemd/system/containerd.service.d/http-proxy.conf
```
```vi
[Service]
Environment="HTTP_PROXY=http://127.0.0.1:7890/"
Environment="HTTPS_PROXY=http://127.0.0.1:7890/"
```
### 重启containerd
```shell
sudo systemctl daemon-reload
sudo systemctl restart containerd
```
### 检查 是否设置成功
```shell
sudo systemctl status containerd
systemctl show containerd --property Environment
```
### 拉取测试
```shell
ctr image pull docker.io/library/nginx:latest
crictl pull docker.io/library/nginx:latest
```



#### 2. 在k8s中设置代理

```shell
sudo vi /etc/systemd/system/kubelet.service.d/10-kubeadm.conf
```
```vi
[Service]
Environment="HTTP_PROXY=http://127.0.0.1:7890/"
```

### 重启kubelet
```shell
sudo systemctl daemon-reload
sudo systemctl restart kubelet
```

```
helm upgrade --install -n kubesphere-system --create-namespace ks-core https://charts.kubesphere.io/main/ks-core-1.1.2.tgz --debug --wait --set global.imageRegistry=swr.cn-southwest-2.myhuaweicloud.com/ks --set extension.imageRegistry=swr.cn-southwest-2.myhuaweicloud.com/ks
```
helm -n kubesphere-system uninstall ks-core --no-hooks

kubectl get all kubesphere-system

kubectl delete pod -n kubesphere-system --grace-period=0 --force --all


etcd --listen-client-urls=http://192.168.110.108:2379 \
   --advertise-client-urls=http://192.168.110.108:2379