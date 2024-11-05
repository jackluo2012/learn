### 安装nvc dcgm-exporter 的监 控
#### 1. 安装dcgm-exporter
[官方的文档地址](https://developer.nvidia.com/dcgm)


[github地址](https://github.com/NVIDIA/gpu-monitoring-tools)

### 安装
```bash
helm repo add gpu-helm-charts \
  https://nvidia.github.io/gpu-monitoring-tools/helm-charts

helm repo update  

helm install --generate-name gpu-helm-charts/dcgm-exporter
```