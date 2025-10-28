# QUANTAXIS 2.1.0-alpha2

<div align="center">

**⭐ 自己学习！ fork [https://github.com/yutiansut](https://github.com/yutiansut)**

</div>

# QUANTAXIS 2.1.0 安装指南

## 🔧 环境检查

### 1. 检查 Python 版本

```bash
python3 --version
# 本次安装环境: Python 3.11.14
```

### 2. 检查 MongoDB 状态

```bash
docker ps | grep mongo
# 确认 MongoDB 容器正在运行
# 9a0cf06c9738   mongo:6 "docker-entrypoint.s…"   18 hours ago   Up 18 hours 0.0.0.0:27017->27017/tcp                                                 dev-mongo
```

## 🚀 安装步骤

### 第一步：创建项目环境

```bash
# 确认在 QUANTAXIS 项目目录中
cd /home/jackluo/learn/quant/QUANTAXIS
pwd
# 输出: /home/jackluo/learn/quant/QUANTAXIS
```

### 第二步：创建 Python 虚拟环境

```bash
# 创建虚拟环境
python3 -m venv .env

# 激活虚拟环境
source .env/bin/activate

# 升级 pip
pip install --upgrade pip
```

### 第三步：安装 QUANTAXIS
```bash
pip install -e ".[dev]"
# pip install -e .[rust,dev]
```

```
pip install pandas numpy pymongo requests lxml tornado

pip install tushare pytdx akshare

pip install scikit-learn statsmodels alphalens

```