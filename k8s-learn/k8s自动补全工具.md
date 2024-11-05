### kubectl 自动补全

```
yum install bash-completion -y
source /usr/share/bash-completion/bash_completion
source <(kubectl completion bash)
vi .bashrc
# 加入
source <(kubectl completion bash)
```

```
export KKZONE=cn
helm upgrade --install -n kubesphere-system --set global.imageRegistry=swr.cn-southwest-2.myhuaweicloud.com/ks --set extension.imageRegistry=swr.cn-southwest-2.myhuaweicloud.com/ks  --create-namespace ks-core https://charts.kubesphere.io/main/ks-core-1.1.2.tgz --debug --wait
```

