### 安装nginx-ingress
```
# 下载nginx-ingress helm 
wget https://github.com/kubernetes/ingress-nginx/releases/download/helm-chart-4.11.2/ingress-nginx-4.11.2.tgz
# 解压
tar -zxvf ingress-nginx-4.11.2.tgz
# 安装
helm install ingress-nginx ingress-nginx-4.11.2
```
#### 修改values.yaml
```
1. 修改hostNetwork: true  # 使用主机网络
2. 修改dnsPolicy: ClusterFirstWithHostNet  # 使用集群优先，主机网络
3. kind: DaemonSet  # 修改为 DaemonSet # 保证在每个节点上运行一个 Pod，稳定性高
4. 关闭所有的镜像的 digest ## 镜像的 digest 是镜像的唯一标识，每次镜像更新都会导致 digest 变化，导致镜像拉取失败
5. - ingressClassResource.default=true  #开启默认的 ingressClass

```
### 创建 命名空间
```
kubectl create namespace ingress
```
### 替换掉官方的镜像
```
vi values.yaml
:%s/registry.k8s.io/m.daocloud.io\/registry.k8s.io/g
```

### 安装
```
helm install ingress-nginx --namespace ingress . -f values.yaml
```
### 查看
```
kubectl get pods --namespace ingress
```
### 卸载
```
helm uninstall ingress-nginx --namespace ingress
```
### 监控变化
```
kubectl get pods --namespace ingress -w
```
### ingress Http 代理 访问
#### deployment、service、ingress yaml 文件
```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ingress-nginx-www1
spec:
  replicas: 1
  selector:
    matchLabels:
        hostname: www1
  template: 
    metadata:
      labels:
        hostname: www1
    spec:
      containers:
        - name: nginx
          image: m.daocloud.io/docker.io/nginx:latest
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: ingress-nginx-www1
spec:
  selector:
    hostname: www1
  ports:
    - name: http    
      port: 80
      targetPort: 80
      protocol: TCP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-nginx-www1
  namespace: ingress
spec:
  ingressClassName: nginx
  rules:
    - host: www1.test.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: ingress-nginx-www1
                port:
                  number: 80
```
### 创建
```
kubectl apply -f ingress.yaml
```
### 查看
```
kubectl get ingress -n ingress
```
### 查看部署在哪台服务器上
```
kubectl get pods -n ingress -o wide
[root@master1 ~]# kubectl get pod -n ingress -o wide
NAME                                        READY   STATUS    RESTARTS   AGE   IP              NODE    NOMINATED NODE   READINESS GATES
ingress-nginx-controller-749867684d-hgqzm   1/1     Running   0          45m   192.168.152.3   node1   <none>           <none>

```
直接访问
```
http://192.168.152.3
```
### Ingress Http 代理 访问
#### deployment、service、ingress yaml 文件
```yaml   ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-nginx-ssl
  namespace: default
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  rules:
    - host: ssl1.test.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: ingress-nginx-ssl
                port:
                  number: 80
  tls:
    - hosts:
        - ssl1.test.com
      secretName: ssl1-test-com
```

```yaml  deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ingress-nginx-ssl
spec:
  replicas: 1
  selector:
    matchLabels:
      hostname: ssl1
  template:
    metadata:
      labels:
        hostname: ssl1
    spec:
      containers:
        - name: nginx
          image: m.daocloud.io/docker.io/nginx:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: ingress-nginx-ssl
spec:
  selector:
    hostname: ssl1
  ports:
    - port: 80
      targetPort: 80
      protocol: TCP
```
### 创建证书
```
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout tls.key -out tls.crt -subj "/CN=ssl1.test.com/O=ssl1.test.com"
```
### 创建 secret
```
kubectl create secret tls ssl1-test-com --cert=tls.crt --key=tls.key -n default
```

### 删除服务 
```
kubectl delete svc ingress-nginx-www1
kubectl delete ingress -all
kubectl delete svc ingress-nginx-ssl
kubectl delete -f ingress.yaml
kubectl delete -f deployment.yaml
kubectl delete -f service.yaml
```



### 创建
```
kubectl apply -f ingress.yaml
kubectl apply -f secret.yaml
kubectl apply -f service.yaml

### 关于 dnsPolicy
#### ClusterFirstWithHostNet:
- 当 Pod 的 hostNetwork 设置为 true 时，使用该 DNS 策略。
- 这意味着 Pod 的网络命名空间与主机共享，Pod 使用主机的网络栈。
- 在此配置下，Pod 将首先尝试通过主机上的 DNS 解析 DNS 请求。如果主机上没有找到，则会将请求发送到 kube-dns 服务，由 kube-dns 服务进行处理。
- 这种策略适用于需要与主机网络共享的特殊情况，但它不会为 Pod 提供专用的 DNS 解析功能.
#### ClusterFirst:
- 这是 Kubernetes 中默认的 DNS 策略,
- 当 Pod 的 hostNetwork 设置为 false 或未设置时，使用该策略。
- 在此策略下，Pod 首先尝试通过 kube-dns 服务解析 DNS 请求。如果 kube-dns 无法解析，则会向上级 DNS 服务器继续发起请求。
- 这种策略适用于大多数情况，其中 Pod 需要使用 Kubernetes 集群的 DNS 服务解析其他 Pod 或服务的主机名。

