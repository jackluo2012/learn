# k8s 常用命令
```
kubectl get nodes -o wide # 查看节点信息
kubectl get pods -o wide # 查看pod信息
kubectl get services -o wide # 查看service信息
kubectl get deployments -o wide # 查看deployment信息
kubectl get statefulsets -o wide # 查看statefulset信息
kubectl get configmaps -o wide # 查看configmap信息
kubectl get secrets -o wide # 查看secret信息
kubectl get events -o wide # 查看事件信息
kubectl get nodes -o wide # 查看节点信息
# 查看容器日志
kubectl logs <pod-name> # 查看指定 Pod 的日志
kubectl logs <pod-name> -c <container-name> # 查看 Pod 中指定容器的日志
kubectl logs -f <pod-name> # 实时查看 Pod 的日志
kubectl logs --tail=20 <pod-name> # 查看 Pod 最后 20 行日志
kubectl logs --since=1h <pod-name> # 查看 Pod 最近 1 小时的日志
kubectl logs <pod-name> > pod.log # 将 Pod 的日志输出到文件
kubectl logs -l app=nginx # 查看带有特定标签的所有 Pod 的日志
# 进入容器内部
kubectl exec -it task-pv-pod -- /bin/bash

```
### kubectl get pod
-A,--a11-namespaces 查看当前所有名称空间的资源
-n 指定名称空间，默认值 default，kube-system 空间存放是当前组件资源
--show-labels查看当前的标签
-1 筛选资源，key、key=value
-o wide 详细信息包括 IP、分配的节点
-W 监视，打印当前的资源对象的变化部分


# 査看 pod 内部容器的 日志
kubectl logs podName -c cName
#查看资源对象的详细描述
kubectl describe pod podName
#删除资源对象
kubectl delete kindName obiName--a11 删除当前所有的资源对象


## containerd 常用命令
```
# 查看 containerd 版本
ctr version

# 列出所有容器
ctr containers list

# 列出所有镜像
ctr images list

# 拉取镜像
ctr images pull docker.io/library/nginx:latest

# 删除镜像
ctr images rm docker.io/library/nginx:latest

# 创建并运行容器
ctr run --rm -d docker.io/library/nginx:latest nginx-test

# 停止容器
ctr tasks kill nginx-test

# 删除容器
ctr containers rm nginx-test

# 查看容器日志
ctr tasks logs nginx-test

# 进入容器
ctr tasks exec --exec-id $RANDOM -t nginx-test sh

# 查看 containerd 服务状态
systemctl status containerd

# 重启 containerd 服务
systemctl restart containerd

```

## 节点管理

### 查看节点信息

