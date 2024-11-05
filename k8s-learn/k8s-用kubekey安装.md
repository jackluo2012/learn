### 安装kubekey
本示例包括以下三台主机，其中主节点充当任务机。

主机 IP	主机名	角色
192.168.152.2	control plane	control plane, etcd
192.168.152.3	node1	worker
192.168.152.4	node2	worker

### 设置主节点
```
hostnamectl set-hostname k8s-master01
hostnamectl set-hostname k8s-node01
hostnamectl set-hostname k8s-node02
```

### 时区
```
timedatectl set-timezone Asia/Shanghai
```

### 关闭防火墙
```
systemctl stop firewalld
systemctl disable firewalld
```
### 安装
```
export KKZONE=cn
curl -sfL https://get-kk.kubesphere.io | sh -

```

### 手动下载 安装包，并执行以下最新 操作命令
```
./kk create config --with-kubernetes v1.31.0 --with-kubesphere
```
### 使用配置文件创建集群
```
export KKZONE=cn
./kk create cluster -f config-sample.yaml
```
### 查看用的contanis 运行时的
```
 kubectl get nodes -o wide

 NAME      STATUS   ROLES           AGE   VERSION   INTERNAL-IP     EXTERNAL-IP   OS-IMAGE                      KERNEL-VERSION                 CONTAINER-RUNTIME
master1   Ready    control-plane   46m   v1.31.0   192.168.152.2   <none>        Rocky Linux 9.4 (Blue Onyx)   5.14.0-427.13.1.el9_4.x86_64   containerd://1.7.13
node1     Ready    worker          46m   v1.31.0   192.168.152.3   <none>        Rocky Linux 9.4 (Blue Onyx)   5.14.0-427.13.1.el9_4.x86_64   containerd://1.7.13
node2     Ready    worker          46m   v1.31.0   192.168.152.4   <none>        Rocky Linux 9.4 (Blue Onyx)   5.14.0-427.13.1.el9_4.x86_64   containerd://1.7.13

 ```
 ### 配置加速
 ```
vi /etc/containerd/config.toml

 endpoint = ["https://docker.m.daocloud.io"]
sudo systemctl restart containerd
 ```