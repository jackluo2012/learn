### kubeadm
kubeadm 是 Kubernetes 官方提供的一个工具，用于在裸机或虚拟机上快速部署 Kubernetes 集群。它简化了 Kubernetes 集群的安装过程，使得用户可以轻松地创建一个高可用性和可扩展的 Kubernetes 集群。

#### 安装 kubeadm
- 优势
    1. 简单易用
    2. 自动化
- 劣势
    1. 依赖于 Docker
    2. 依赖于网络插件
    3. 依赖于 CNI 插件
    4. 依赖于 kubeadm 配置
一主两从

Ikuai 路由器  
- ikuai 
    1、2.设置LAN/WAN地址
    2、0 设置LAN1地址 -> 输入lan1的ip地址:192.168.152.200/255.255.255.0 # 设置一个未被 占用 的ip地址


- master 节点 192.168.152.11 
    CPU >=2核
    RAM >=4G
    NIC >=1  1张网卡
    DISK >=100GB 
- node 节点 192.168.152.12 ，192.168.152.13
    CPU >=2核
    RAM >=4G
    NIC >=1  1张网卡
    DISK >=100GB 

# 先关闭 master 节点 node 节点 的 net网卡

## 设置 getway 和 dns
```
vi /etc/NetworkManager/system-connections/ens160.nmconnection
[ ipv4 ]
method=manual
address1=192.168.152.11/24,192.168.152.200
dns=114.114.114.114;8.8.8.8;

# 关闭另一张网卡
vi /etc/NetworkManager/system-connections/ens192.nmconnection
# 将 autoconnect=true 改为 autoconnect=false
autoconnect=false

# 重启网络服务
systemctl restart NetworkManager
```

1. 在所有节点上安装 Docker 和 kubeadm
2. 初始化主节点
3. 安装网络插件
4. 安装网络插件


### 二进制安装
    组件变成系统进程的方式运行。

### 关闭swap 分区 
```
swapoff -a
sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
# 修改主机名
hostnamectl set-hostname k8s-master01
hostnamectl set-hostname k8s-node01
hostnamectl set-hostname k8s-node02

# 修改 /etc/hosts
192.168.152.11 k8s-master01 m1
192.168.152.12 k8s-node01 n1
192.168.152.13 k8s-node02 n2
192.168.152.14 harbor

```

### 安装ipvs
```
yum install -y ipvsadm

# 开启路由转发
echo 'net.ipv4.ip_forward = 1' >> /etc/sysctl.conf
sysctl -p

```
### 安装 cri-docker
```
wget https://github.com/Mirantis/cri-dockerd/releases/download/v0.3.15/cri-dockerd-0.3.15.amd64.tgz
tar -xvf cri-dockerd-0.3.15.amd64.tgz
cp cri-dockerd /usr/bin/
chmod +x /usr/bin/cri-dockerd

```
# 配置cri-docker 服务 
cat <<EOF > /etc/systemd/system/cri-docker.service
[Unit]
Description=CRI Interface for Docker Application
Documentation=https://github.com/Mirantis/cri-dockerd
After=network-online.target firewalld.service docker.service
Wants=network-online.target
Requires=cri-docker.socket

[Service]
Type=notify
ExecStart=/usr/bin/cri-dockerd --network-plugin=cni --pod-infra-container-image=k8s.m.daocloud.io/pause:3.9
ExecReload=/bin/kill -s HUP $MAINPID
TimeoutSec=0
RestartSec=2
Restart=always
StartLimitBurst=3
StartLimitInterval=60s
LimitNOFILE=infinity
LimitNPROC=infinity
LimitCORE=infinity
TasksMax=infinity
Delegate=yes
KillMode=process

[Install]
WantedBy=multi-user.target
EOF
# 添加 cri-docker 套接字
cat <<EOF > /usr/lib/systemd/system/cri-docker.socket
[Unit]
Description=CRI Docker Socket for the API
Documentation=https://github.com/Mirantis/cri-dockerd
After=network.target
PartOf=cri-docker.service

[Socket]
ListenStream=%t/cri-dockerd.sock
SocketMode=0660
SocketUser=root
SocketGroup=docker

[Install]
WantedBy=sockets.target
EOF

# 启动服务
systemctl daemon-reload
systemctl enable cri-docker
systemctl start cri-docker
systemctl is-active cri-docker

## 设置k8s 镜像源
```
cat <<EOF > /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://mirrors.aliyun.com/kubernetes/yum/repos/kubernetes-el7-x86_64/
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://mirrors.aliyun.com/kubernetes/yum/doc/yum-key.gpg https://mirrors.aliyun.com/kubernetes/yum/doc/rpm-package-key.gpg
EOF
```
## 安装 kubeadm kubelet kubectl
```
yum install -y kubelet kubeadm kubectl
systemctl enable kubelet && systemctl start kubelet
```






