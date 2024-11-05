#### k8s-containerd 常用命令 crictl（kubernetes）主要用于k8s
### 配置镜像源配置
[text](https://gist.github.com/y0ngb1n/7e8f16af3242c7815e7ca2f0833d3ea6)
```
vim /etc/containerd/config.toml
sudo systemctl restart containerd
```

```
crictl -n k8s.io namespaces ls #查看所有的命名空间
```
#### 查看，所有的镜像 
```
crictl images ls
```
### 拉取镜像
```
ctr -n k8s.io images pull m.daocloud.io/docker.io/library/nginx:
```
### 导入镜像
```
ctr -n k8s.io image import 
```

请格式化以下 Kubernetes 资源定义:

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: nfs-client-provisioner
  namespace: default

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: nfs-client-provisioner-clusterrole
rules:
  - apiGroups: [""]
    resources: ["persistentvolumes"]
    verbs: ["get", "list", "watch", "create", "delete"]
  - apiGroups: [""]
    resources: ["persistentvolumeclaims"]
    verbs: ["get", "list", "watch", "update"]
  - apiGroups: ["storage.k8s.io"]
    resources: ["storageclasses"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["events"]
    verbs: ["list", "watch", "create", "update", "patch"]
  - apiGroups: [""]
    resources: ["endpoints"]
    verbs: ["create", "delete", "get", "list", "watch", "patch", "update"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: nfs-client-provisioner-clusterrolebinding
subjects:
  - kind: ServiceAccount
    name: nfs-client-provisioner
    namespace: default
roleRef:
  kind: ClusterRole
  name: nfs-client-provisioner-clusterrole
  apiGroup: rbac.authorization.k8s.io

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: leader-locking-nfs-client-provisioner
  namespace: default
rules:
  - apiGroups: [""]
    resources: ["endpoints"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: leader-locking-nfs-client-provisioner
  namespace: default
subjects:
  - kind: ServiceAccount
    name: nfs-client-provisioner
    namespace: default
roleRef:
  kind: Role
  name: leader-locking-nfs-client-provisioner
  apiGroup: rbac.authorization.k8s.io
```
apiVersion: v1kind: ServiceAccountmetadata:  name: nfs-client-provisioner  namespace: default---#创建集群角色apiVersion: rbac.authorization.k8s.io/v1kind: ClusterRolemetadata:  name: nfs-client-provisioner-clusterrolerules:  - apiGroups: [""]    resources: ["persistentvolumes"]    verbs: ["get", "list", "watch", "create", "delete"]  - apiGroups: [""]    resources: ["persistentvolumeclaims"]    verbs: ["get", "list", "watch", "update"]  - apiGroups: ["storage.k8s.io"]    resources: ["storageclasses"]    verbs: ["get", "list", "watch"]  - apiGroups: [""]    resources: ["events"]    verbs: ["list", "watch", "create", "update", "patch"]  - apiGroups: [""]    resources: ["endpoints"]    verbs: ["create", "delete", "get", "list", "watch", "patch", "update"]---#集群角色绑定apiVersion: rbac.authorization.k8s.io/v1kind: ClusterRoleBindingmetadata:  name: nfs-client-provisioner-clusterrolebindingsubjects:- kind: ServiceAccount  name: nfs-client-provisioner  namespace: defaultroleRef:  kind: ClusterRole  name: nfs-client-provisioner-clusterrole  apiGroup: rbac.authorization.k8s.io---kind: RoleapiVersion: rbac.authorization.k8s.io/v1metadata:  name: leader-locking-nfs-client-provisioner  namespace: defaultrules:  - apiGroups: [""]    resources: ["endpoints"]    verbs: ["get", "list", "watch", "create", "update", "patch"]---kind: RoleBindingapiVersion: rbac.authorization.k8s.io/v1metadata:  name: leader-locking-nfs-client-provisioner  namespace: defaultsubjects:  - kind: ServiceAccount    name: nfs-client-provisioner    # replace with namespace where provisioner is deployed    namespace: defaultroleRef:  kind: Role  name: leader-locking-nfs-client-provisioner  apiGroup: rbac.authorization.k8s.io
```


apiVersion: v1
kind: PersistentVolume
metadata:
  name: test-nfs-static-pv
spec:
  capacity:
    storage: 1Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Recycle
  nfs:
    path: /data/nfs
    server: 172.139.20.170


apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-nfs-static-pvc
spec:
  accessModes:
    - ReadWriteMany
  volumeMode: Filesystem
  resources:
    requests:
      storage: 1Gi


apiVersion: apps/v1
kind: Deployment
metadata:
  name: tools
spec:
  replicas: 1
  selector:
    matchLabels:
      app: tools
  template:
    metadata:
      labels:
        app: tools
    spec:
      containers:
      - name: tools
        image: registry.cn-guangzhou.aliyuncs.com/jiaxzeng6918/tools:v1.1
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: test-nfs-static-pvc      