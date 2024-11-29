### 通过 调用k8s 接口 直接 部署 服务
 - 通过 web 界面 上传 镜像 到服务 器
 - 将镜像推送到 registry 镜像仓库
 - 通过 k8s 接口部署服务
 - 通过 k8s 接口暴露服务


#### 安装依赖
```bash
npm install express @kubernetes/client-node
```
#### 启动服务
```bash
node app.js
```
#### 测试部署 API
```bash
curl -X POST http://localhost:3000/deploy \
-H "Content-Type: application/json" \
-d '{"imageName": "nginx:latest", "containerPort": 80}'
```

#### 返回的json结果
```
{
  "deploymentName": "app-1698598100000-deployment",
  "serviceName": "app-1698598100000-service",
  "servicePort": 32345,
  "nodeIp": "192.168.1.100",
  "message": "Service 'app-1698598100000-service' is exposed on node '192.168.1.100:32345'"
}
```



#### 安装 harbor 镜像仓库
```bash
helm repo add harbor https://helm.goharbor.io
helm repo update
helm install harbor harbor/harbor --namespace harbor --set expose.type=nodePort --set expose.tls.enabled=false --set persistence.enabled=true
helm install harbor harbor/harbor --namespace harbor --set expose.type=nodePort --set expose.hostname=192.168.110.116 --set expose.tls.enabled=false --set persistence.enabled=true

helm install harbor harbor/harbor --namespace harbor \
  --set expose.type=nodePort \
  --set expose.hostname=192.168.110.116 \
  --set expose.tls.enabled=false \
  --set persistence.enabled=true

helm uninstall -n harbor harbor harbor/harbor
```
```bash
kubectl get pods -n harbor
kubectl get svc -n harbor

```
#### harbo 帐号：admin 密码：Harbor12345



### harbor 如果麻烦，请使用 docker 官方的部署 registry



### 使用
```bash
docker tag io3d-server:latest 192.168.110.116:30500/vendor/io3d-server:latest
docker push 192.168.110.116:30500/vendor/io3d-server:latest
```
### 查看镜像仓库中的镜像
```bash
curl -i 192.168.110.116:30500/v2/_catalog
```

### 通过 调用k8s 接口 直接 部署 服务
```bash
curl -X POST http://localhost:3000/deploy \
-H "Content-Type: application/json" \
-d '{"imageName": "192.168.110.116:30500/vendor/io3d-server:latest", "containerPort": 8100}'
```


### 修改k8s 配置文件
```bash
sudo vi /etc/containerd/config.toml

#####
[plugins."io.containerd.grpc.v1.cri".registry]
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
    [plugins."io.containerd.grpc.v1.cri".registry.mirrors."192.168.110.116:30500"]
      endpoint = ["http://192.168.110.116:30500"]
#####

sudo systemctl restart containerd
```
```bash
apiVersion: apps/v1
kind: Deployment
metadata:
  name: image-pull-test
spec:
  replicas: 1
  selector:
    matchLabels:
      app: image-pull-test
  template:
    metadata:
      labels:
        app: image-pull-test
    spec:
      containers:
        - name: test-container
          image: 192.168.110.116:30500/my-image:latest  # 你的私有镜像地址
          imagePullPolicy: Always
```
