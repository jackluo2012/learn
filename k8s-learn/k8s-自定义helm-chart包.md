### 自定义helm-chart包
```bash
## 创建 mychart的包
helm create mychart
### 安装
helm install full-coral ./mychart

### 卸载发布包
helm uninstall full-coral
```
```bash
### 删除 
rm -rf mychart/templates/*

```
#### 创建 mychart/templates/configmap.yaml
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mychart-configmap
data:
  myvalue: "Hello World"
```

### 调试用
```bash 
helm install --generate-name --dry-run --debug mychart/
helm install --generate-name --dry-run --debug mychart/charts/mysubchart/
```