### 使用 Service 暴露你的应用
```
kubectl get pods
```
### 查询集群中的Service:
```
kubectl get services
```
###  要创建一个新的 Service 然后暴露给外部流量，我们将使用 expose 命令，并将 NodePort 作为参数
```
kubectl expose deployment/kubernetes-bootcamp --type="NodePort" --port 8080
```

### 查看对应的端口

```
kubectl describe services/kubernetes-bootcamp
```

### 创建一个名为 NODE_PORT 的环境变量，它的值为所分配的 Node 端口
```
export NODE_PORT="$(kubectl get services/kubernetes-bootcamp -o go-template='{{(index .spec.ports 0).nodePort}}')"
echo "NODE_PORT=$NODE_PORT"
```

### 第二步：使用标签
```
kubectl describe deployment
```

### 使用这个标签来查询 Pod 列表
```
kubectl get pods -l app=kubernetes-bootcamp
```
### 你可以用同样的方法列出现有的 Service
```
kubectl get services -l app=kubernetes-bootcamp
```

### 要应用一个新的标签，我们使用 label 子命令，接着是对象类型、对象名称和新的标签：
```
kubectl label pods "$POD_NAME" version=v1
```