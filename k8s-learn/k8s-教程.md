### 教程

### 创建 Deployment
```bash
kubectl create deployment hello-node --image=k8s.m.daocloud.io/e2e-test-images/agnhost:2.39 -- /agnhost netexec --http-port=8080
```
### 查看 Pod ,查看集群事件 查看 kubectl 配置
```
kubectl get pods

kubectl get events

kubectl config view


kubectl logs
```

### 创建 Service
```
kubectl expose deployment hello-node --type=LoadBalancer --port=8080


kubectl get services

root@iotree-desktop:/home/iotree3d-images/devops/demo# kubectl get services
NAME         TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
hello-node   LoadBalancer   10.233.62.206   <pending>     8080:31544/TCP   3m39s


```

### 清理
```
kubectl delete service hello-node
kubectl delete deployment hello-node
```

### 部署一个应用
```
kubectl create deployment kubernetes-bootcamp --image=gcr.m.daocloud.io/google-samples/kubernetes-bootcamp:v1
```

### 在终端中显示应用
```
kubectl proxy
export POD_NAME="$(kubectl get pods -o go-template --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}')"
curl http://localhost:8001/api/v1/namespaces/default/pods/$POD_NAME:8080/proxy/
```

### 查看容器日志
```
kubectl logs "$POD_NAME"
#我们不需要指定容器名称，因为在 Pod 内只有一个容器。
```

### 在容器上执行命令
```
kubectl exec "$POD_NAME" -- env

kubectl exec -ti $POD_NAME -- bash
```