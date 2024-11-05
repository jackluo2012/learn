### 1. 什么是Kubernetes

Kubernetes是一个开源的容器编排平台，用于自动化应用程序的部署、扩展和管理。它提供了一个强大的基础设施来运行和管理容器化应用程序，无论是在本地环境还是在云环境中。

### 2. 安装k8s

#### 2.1 安装k8s
#### 下载Rocky Linux 9.4

```bash
https://download.rockylinux.org/pub/rocky/9/isos/x86_64/Rocky-9.4-x86_64-minimal.iso
```

### Pod: 一个Pod是一个容器化应用程序的实例，它是Kubernetes中最小的可部署单元。一个Pod可以包含一个或多个容器，它们共享相同的网络命名空间和存储卷。

### 创建虚拟机
 CUP 2C2
 内存 4G
 硬盘 100G
 网络 仅主机模式 
     NET模式 NIC

### 安装虚拟机
#### 手动分区
- /boot 800M
- swap 4G
- / 95G


### 二、环境初始化
```bash
# 网卡配置  需查看vm虚拟机上的网卡信息 

# 192.168.152.128/24 
vi /etc/NetworkManager/system-connections/ens160.nmconnection
[ ipv4 ]
method=manual
address1=192.168.152.11/24
# 重启网络服务
systemctl restart NetworkManager
```
### Rocky 替换成阿里云源
```bash
# 备份原文件
cd /etc/yum.repos.d
mkdir bak
cp *.repo bak/
# 下载阿里云源
sed -e 's|^mirrorlist=|#mirrorlist=|g' \
     -e 's|^#baseurl=http://dl.rockylinux.org/$contentdir|baseurl=https://mirrors.aliyun.com/rockylinux|g' \
     -i.bak \
     /etc/yum.repos.d/rocky*.repo
dnf makecache
```
### 防火墙
```bash
systemctl stop firewalld
systemctl disable firewalld
```
```
# 安装 iptables-services
dnf install iptables-services
# 启动 iptables-services
systemctl start iptables
systemctl enable iptables
iptables -F # 清空所有规则
service iptables save # 保存规则
```
### 关闭SELinux
```bash
# 永久关闭
sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/selinux/config
# 临时关闭
setenforce 0
#查看是否禁用
grubby --info DEFAULT
# 更新内核
grubby --update-kernel=DEFAULT --args="selinux=0"
```
### 设置系统时间
```bash
timedatectl set-timezone Asia/Shanghai
```
