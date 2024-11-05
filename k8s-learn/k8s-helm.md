### 一、Helm 简介
Helm 是 Kubernetes 的包管理工具，类似于 Docker 的 Docker Hub。Helm 可以帮助我们更方便地管理和部署 Kubernetes 应用。

### 二、Helm 安装
1. 下载 Helm
```
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh
```
### 添加 Helm 仓库
```
helm repo add community https://release.daocloud.io/chartrepo/community
helm repo update
```
### 安装应用
```
helm install community/tomcat --generate-name
```
### 查看应用
```
helm list -n default
kubectl get svc
kubectl get pod
kubectl describe pod tomcat-1696666666-111111
```
### 查
```
helm show values community/tomcat
helm show chart community/tomcat
```
### 删除应用
```
helm uninstall tomcat-1696666666-111111
```
### 二、三大概念    
### 安装前自定义 chart
```
helm show values community/tomcat

vi values.yaml
# 只改有用的
service:
    type:NodePort 
helm install -f values.yaml community/tomcat --generate-name

```
### 更多安装方法
he1m insta11 命令可以从多个来源进行安装
·chart 的仓库(如上所述)
## 本地 chart压缩包(helm insta1l foo foo-0.1.1.tgz)解压后的 chart目录(helm insta1l foo path/to/foo)
完整的 URL(helm insta11 foo https://example.com/charts/foo-1.2.3.tgz)

### 制作chart

1. 创建一个新的chart
```
helm create mychart
```
2. 修改chart
```

```

