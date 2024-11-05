### 一、安装 NFS 服务器
```
# 每个节点都需要安装
yum install -y nfs-utils rpcbind # 安装 NFS 和 RPCBIND 服务
```
### 在 master 节点上创建共享目录
```
mkdir -p /nfsdata
chmod 666 /nfsdata
chown nobody /nfsdata
```
### 三、配置 NFS 服务
```
echo "/nfsdata *(rw,sync,no_root_squash,no_all_squash)" >> /etc/exports
exportfs -r
systemctl enable rpcbind
systemctl enable nfs-server
systemctl start rpcbind
systemctl start nfs-server
```
```bash #创建10个目录
cd /nfsdata && mkdir {1..10}

vi /etc/exports
/nfsdata/1 *(rw,sync,no_root_squash,no_all_squash)
/nfsdata/2 *(rw,sync,no_root_squash,no_all_squash)
/nfsdata/3 *(rw,sync,no_root_squash,no_all_squash)
/nfsdata/4 *(rw,sync,no_root_squash,no_all_squash)
/nfsdata/5 *(rw,sync,no_root_squash,no_all_squash)
/nfsdata/6 *(rw,sync,no_root_squash,no_all_squash)
/nfsdata/7 *(rw,sync,no_root_squash,no_all_squash)
/nfsdata/8 *(rw,sync,no_root_squash,no_all_squash)
/nfsdata/9 *(rw,sync,no_root_squash,no_all_squash)
/nfsdata/10 *(rw,sync,no_root_squash,no_all_squash)
```
### 查看 共享 目录 
```bash
showmount -e 192.168.152.2
# 192.168.152.3 中挂载
mount -t nfs 192.168.152.2:/nfsdata/1 /mnt
# 查看共享地址
showmount -e 192.168.152.2
```

