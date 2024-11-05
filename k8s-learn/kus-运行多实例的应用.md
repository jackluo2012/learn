### 运行多实例的应用

### Service，然后运行以下命令来创建一个新的 type 设置为 LoadBalancer 的 Service
```
kubectl expose deployment/kubernetes-bootcamp --type="LoadBalancer" --port 8080
```
### 查看由 Deployment 创建的 ReplicaSet
```
kubectl get rs
```
### 接下来，让我们扩容 Deployment 到 4 个副本
```
kubectl scale deployments/kubernetes-bootcamp --replicas=4
```
### 要再次列举出你的 Deployment
```
root@iotree-desktop:/home/data/server/io-server/build# kubectl get deployments
NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
kubernetes-bootcamp   4/4     4            4           4h12m
```
### 负载均衡
```
kubectl describe services/kubernetes-bootcamp
```
###
```
export NODE_PORT="$(kubectl get services/kubernetes-bootcamp -o go-template='{{(index .spec.ports 0).nodePort}}')"
echo NODE_PORT=$NODE_PORT
```

### 缩容
```
kubectl scale deployments/kubernetes-bootcamp --replicas=2
```

### 要列举 Deployment 以检查是否应用了更改
```

```