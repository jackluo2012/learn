### 命令集
### 获取指定 命名空间下的镜像

### 常用nerdctl命令

```
nerdctl images --namespace=k8s.io
nerdctl -n=k8s.io images
```
### nerdctl 配置文件中指定 nerdctl 默认使用 k8s.io namespace
```
mkdir  /etc/nerdctl/
cat >> /etc/nerdctl/nerdctl.toml << EOF
namespace = "k8s.io"
EOF
```

### nerdctl run和 docker run 类似可以使用 nerdctl run 命令运行容器，例如：
```
nerdctl run -d -p 80:80 --name=nginx --restart=always nginx:alpine
```
### 同样也可以使用 exec 命令执行容器相关命令
```
nerdctl exec -it nginx /bin/sh
```
### nerdctl ps：列出容器 ,nerdctl logs：获取容器日志, nerdctl stop：停止容器, nerdctl rm：删除容器
```
nerdctl ps
nerdctl logs -f nginx
nerdctl stop nginx
```
### erdctl images：镜像列表
```
nerdctl images
```

### nerdctl tag：镜像标签
```
nerdctl tag nginx:alpine harbor.boysec.cn/course/nginx:alpine
```
### nerdctl pull：拉取镜像 nerdctl push：推送镜像
```
```