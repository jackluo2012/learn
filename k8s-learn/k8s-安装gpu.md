### k8s 安装gpu
### containerd 使用
```
nerdctl images 
```
### 导入镜像
```
nerdctl load -i <镜像文件名>

```
### 改名镜像
```
nerdctl tag old-image-name:old-tag new-image-name:new-tag
```
### 删除 没有被引用的镜像
```
# 被改名的也被清理
nerdctl image prune --all
```
###
```
nerdctl tag nvcr.io/nvidia/gpu-operator:v23.9.0 nvcr.m.daocloud.io/nvidia/gpu-operator:v23.9.0
```
### 这个是官方文档 
```
https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/getting-started.html
```

### 大概流程是： 先安装 device-plugin-framerwork 插件 -> 再在k8s 启用插件，再用helm 包安装 gpu-operator，->并且将 node 打上 gpu服务 的标签，就完事了。
```
官方文档 
[官方文档](https://github.com/NVIDIA/gpu-operator)
```
### 先装 NVIDIA Container Toolkit
```
安装文档 的地址 ,这个主要是用装 k8s 支持 gpu
[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
```

### 再按照这个文档 来 上面讲了怎么部署一系列的
[部署](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/getting-started.html)

### 可参考中文 

[text](https://www.lixueduan.com/posts/ai/02-gpu-operator/)

```
kubectl create ns gpu-operator
kubectl label --overwrite ns gpu-operator pod-security.kubernetes.io/enforce=privileged
```
### 确定 NFD 是否已在集群中运行的一种方法是检查节点上的 NFD 标签
```
kubectl get nodes -o json | jq '.items[].metadata.labels | keys | any(startswith("feature.node.kubernetes.io"))
```

```
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia \
    && helm repo update



helm install --wait --generate-name \
    -n gpu-operator \
    nvidia/gpu-operator \
    --set nfd.enabled=false


helm install --wait --generate-name \
    -n gpu-operator --create-namespace \
    nvidia/gpu-operator \
    --set nfd.enabled=false
    
    --set dcgmExporter.enabled=false    
```