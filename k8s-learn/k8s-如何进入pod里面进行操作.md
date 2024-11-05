### 部署pod
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: two-containers
spec:

  restartPolicy: Never

  volumes:
  - name: shared-data
    emptyDir: {}

  containers:

  - name: nginx-container
    image: nginx
    volumeMounts:
    - name: shared-data
      mountPath: /usr/share/nginx/html

  - name: debian-container
    image: debian
    volumeMounts:
    - name: shared-data
      mountPath: /pod-data
    command: ["/bin/sh"]
    args: ["-c", "echo Hello from the debian container > /pod-data/index.html"]

```
### 查看 Pod 和容器的信息
```bash
kubectl get pod two-containers --output=yaml
```
### 进入 nginx 容器的 shell
```bash
kubectl apply -f two-container-pod.yaml
```
### 进入pod中
```
kubectl exec -it two-containers -c nginx-container -- /bin/bash
```