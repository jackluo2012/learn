### k8s 安装nfs 服务 
#### 仓库地址
[仓库地址github：](https://github.com/kubernetes-csi/csi-driver-nfs)
### 自动挂载装驱动
```
helm repo add csi-driver-nfs https://raw.githubusercontent.com/kubernetes-csi/csi-driver-nfs/master/charts
helm install csi-driver-nfs csi-driver-nfs/csi-driver-nfs --namespace kube-system --version v4.9.0
kubectl --namespace=kube-system get pods --selector="app.kubernetes.io/instance=csi-driver-nfs" --watch

```
[教程地址](https://mp.weixin.qq.com/s/cYqXiwIdxQROSPHu7_jh0A)
```
helm install nfs-subdir-external-provisioner community/nfs-subdir-external-provisioner \
    --set storageClass.name=nfs-sc \
    --set nfs.server=192.168.110.108 \
    --set nfs.path=/home/data -n nfs-system
```
### 查看创建的资源
```
kubectl get sc nfs-sc -o wide

NAME     PROVISIONER                                     RECLAIMPOLICY   VOLUMEBINDINGMODE   ALLOWVOLUMEEXPANSION   AGE
nfs-sc   cluster.local/nfs-subdir-external-provisioner   Delete          Immediate           true                   12m
```
### 查看 Deployment
```
kubectl get deployment -n nfs-system -o wide

NAME                              READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS                        IMAGES                                                               SELECTOR
nfs-subdir-external-provisioner   1/1     1            1           13m   nfs-subdir-external-provisioner   registry.k8s.io/sig-storage/nfs-subdir-external-provisioner:v4.0.2   app=nfs-subdir-external-provisioner,release=nfs-subdir-external-provisioner

````

### 查看pod
```
kubectl get pod -n nfs-system -o wide

NAME                                               READY   STATUS    RESTARTS   AGE     IP              NODE             NOMINATED NODE   READINESS GATES
nfs-subdir-external-provisioner-7d956f969b-k7g49   1/1     Running   0          14m     10.233.121.76   iotree-desktop   <none>           <none>
test-nfs-pod                                       1/1     Running   0          9m49s   10.233.121.77   iotree-desktop   <none>           <none>

```

### 创建测试 PVC
```test-nfs-pvc.yaml
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: test-nfs-pvc
spec:
  storageClassName: nfs-sc
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 1Gi
```
### 创建 PVC
```
kubectl apply -f test-nfs-pvc.yaml -n nfs-system
kubectl get pvc -n nfs-system -o wide
```
### 创建测试 Pod
```test-nfs-pod.yaml
kind: Pod
apiVersion: v1
metadata:
  name: test-nfs-pod
spec:
  containers:
  - name: test-nfs-pod
    image: busybox:stable
    command:
      - "/bin/sh"
    args:
      - "-c"
      - "touch /mnt/SUCCESS && sleep 3600"
    volumeMounts:
      - name: nfs-pvc
        mountPath: "/mnt"
  restartPolicy: "Never"
  volumes:
    - name: nfs-pvc
      persistentVolumeClaim:
        claimName: test-nfs-pvc
```
### 创建 Pod   查看 Pod  查看 Pod 挂载的存储
```
kubectl apply -f test-nfs-pod.yaml -n nfs-system
kubectl get pods -n nfs-system -o wide
kubectl exec test-nfs-pod -n nfs-system -- df -h
```


```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pv-claim
spec:
  storageClassName: nfs-sc
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: wordpress-pv-claim
spec:
  storageClassName: nfs-sc
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```