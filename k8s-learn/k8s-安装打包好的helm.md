### k8s-安装打包好的helm charts

```
helm install -n prometheus --generate-name ./kube-prometheus-stack-65.3.1.tgz --values /tmp/kube-prometheus-stack.values





kubectl patch svc kube-prometheus-stack-65-1729480906-grafana \
   -n prometheus \
   --patch "$(cat grafana-patch.yaml)"
```

