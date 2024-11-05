[text](https://kubesphere.io/zh/blogs/kubesphere-terminating-namespace/)


```
helm upgrade --install -n kubesphere-system --create-namespace ks-core https://charts.kubesphere.io/main/ks-core-1.1.2.tgz --debug --wait --set global.imageRegistry=swr.cn-southwest-2.myhuaweicloud.com/ks --set extension.imageRegistry=swr.cn-southwest-2.myhuaweicloud.com/ks
```
```
kubectl patch fluentbit.logging.kubesphere.io fluent-bit -n kubesphere-logging-system --type='merge' -p='{"metadata": {"finalizers": []}}'
```