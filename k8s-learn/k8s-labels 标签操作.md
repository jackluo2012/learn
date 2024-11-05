### k8s-labels 标签操作

#### 添加标签

```shell
kubectl label nodes node01 disktype=ssd
```

#### 删除标签

```shell
kubectl label nodes node01 disktype-
```

#### 修改标签

```shell
kubectl label nodes node01 disktype=ssd --overwrite
```

#### 查看标签

```shell
kubectl get nodes --show-labels 

kubectl get nodes --show-labels  |grep nvidia.com/gpu.deploy.dcgm-exporter
```


```
helm upgrade --install -n kubesphere-system --create-namespace ks-core https://charts.kubesphere.io/main/ks-core-1.1.2.tgz --debug --wait --set global.imageRegistry=swr.cn-southwest-2.myhuaweicloud.com/ks --set extension.imageRegistry=swr.cn-southwest-2.myhuaweicloud.com/ks
```