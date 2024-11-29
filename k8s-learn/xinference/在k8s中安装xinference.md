# 新增xinference仓库
helm repo add xinference https://xorbitsai.github.io/xinference-helm-charts

# 更新仓库，查询可安装的版本
helm repo update xinference
helm search repo xinference/xinference --devel --versions

# 在K8s中安装xinference
helm install xinference xinference/xinference --create-namespace -n xinference --version 0.0.2-v0.14.4

###
ctr -n k8s.io images tag registry.cn-hangzhou.aliyuncs.com/xprobe_xinference/xinference:latest docker.io/xprobe/xinference:v0.14.4 
