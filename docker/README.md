# Docker 开发环境集合

这个项目包含了几个预配置的 Docker Compose 环境，用于不同的开发需求。

## 环境列表

### 1. 基础数据服务环境 (`docker-compose.yml`)
包含常用的数据库和中间件服务。

**服务列表:**
- MySQL 9.0 (端口: 3306)
- PostgreSQL 17 (端口: 5432)
- MongoDB 8.0 (端口: 27017)
- ClickHouse (端口: 8123, 9000)
- Redis (端口: 6379)
- Apache Kafka (端口: 9092)
- ZooKeeper (端口: 2181)
- etcd (端口: 2379, 2380)
- NATS (端口: 4222, 6222, 8222)

**默认认证:**
- 用户名: `devuser`
- 密码: `devpass`
- MySQL root 密码: `admin`

### 2. Web 开发环境 (`web-dev.yml`)
专用于 Web 应用开发，包含前端、后端、数据库和监控。

**服务列表:**
- Node.js 应用环境 (端口: 3000)
- Nginx 开发服务器 (端口: 8080)
- API 网关 (端口: 80, 443)
- MySQL 数据库 (端口: 3306)
- Redis 缓存 (端口: 6379)
- Elasticsearch 搜索 (端口: 9200, 9300)
- RabbitMQ 消息队列 (端口: 5672, 15672)
- Prometheus 监控 (端口: 9090)
- Grafana 仪表板 (端口: 3001)
- Loki 日志收集 (端口: 3100)
- Portainer 容器管理 (端口: 9443)

### 3. 数据分析环境 (`data-analysis.yml`)
专用于数据分析和机器学习项目。

**服务列表:**
- Jupyter Notebook (端口: 8888)
- RStudio (端口: 8787)
- PostgreSQL 数据仓库 (端口: 5432)
- ClickHouse 分析数据库 (端口: 8123, 9000, 9004, 9005)
- MongoDB 文档数据库 (端口: 27017)
- MinIO 对象存储 (端口: 9000, 9001)
- Apache Airflow 工作流 (端口: 8080)
- Apache Spark (Master: 8081, Worker: 7077)
- Superset 数据可视化 (端口: 8088)
- Grafana 监控 (端口: 3000)
- Redis 缓存 (端口: 6379)
- DBeaver 数据库管理 (端口: 8978)
- File Browser 文件管理 (端口: 8082)
- cAdvisor 性能监控 (端口: 8083)

## 使用方法

### 启动环境

```bash
# 启动基础数据服务
docker-compose up -d

# 启动 Web 开发环境
docker-compose -f web-dev.yml up -d

# 启动数据分析环境
docker-compose -f data-analysis.yml up -d
```

### 停止环境

```bash
# 停止基础数据服务
docker-compose down

# 停止 Web 开发环境
docker-compose -f web-dev.yml down

# 停止数据分析环境
docker-compose -f data-analysis.yml down
```

### 查看服务状态

```bash
# 查看基础服务状态
docker-compose ps

# 查看 Web 开发环境状态
docker-compose -f web-dev.yml ps

# 查看数据分析环境状态
docker-compose -f data-analysis.yml ps
```

## 配置说明

### 环境变量配置

大多数服务都使用了默认的开发环境配置。在生产环境中，请修改以下配置：

1. 数据库密码
2. 管理员账户
3. SSL 证书配置
4. 网络安全设置

### 数据持久化

所有服务的数据都存储在 `./data/` 目录下，确保：

1. 备份重要数据
2. 设置适当的文件权限
3. 监控磁盘空间使用

### 网络配置

每个环境都使用独立的 Docker 网络：

- `dev-network` - 基础数据服务
- `web-dev-network` - Web 开发环境
- `analysis-network` - 数据分析环境

## 快速开始示例

### Web 开发示例

```bash
# 启动 Web 开发环境
docker-compose -f web-dev.yml up -d

# 等待服务启动完成
docker-compose -f web-dev.yml ps

# 访问服务
# Node.js 应用: http://localhost:3000
# Nginx 服务器: http://localhost:8080
# Grafana: http://localhost:3001 (admin/admin123)
# Portainer: https://localhost:9443 (admin/admin123)
```

### 数据分析示例

```bash
# 启动数据分析环境
docker-compose -f data-analysis.yml up -d

# 等待服务启动完成
docker-compose -f data-analysis.yml ps

# 访问服务
# Jupyter Notebook: http://localhost:8888
# RStudio: http://localhost:8787 (rstudio/rstudio123)
# Superset: http://localhost:8088 (admin/admin123)
# Grafana: http://localhost:3000 (admin/admin123)
# MinIO Console: http://localhost:9001 (analyst/analyst123456)
```

## 故障排除

### 常见问题

1. **端口冲突**: 如果端口被占用，修改 `docker-compose.yml` 中的端口映射
2. **内存不足**: 对于大数据分析，建议至少 8GB 内存
3. **磁盘空间**: 确保足够的磁盘空间用于数据存储
4. **权限问题**: 确保 Docker 有足够的权限访问挂载目录

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs mysql

# 实时查看日志
docker-compose logs -f redis
```

### 重新构建服务

```bash
# 重新构建并启动服务
docker-compose up -d --build

# 清理并重新创建
docker-compose down -v
docker-compose up -d
```

## 安全注意事项

1. 默认密码仅用于开发环境，生产环境必须修改
2. 不要在生产环境中暴露管理端口到公网
3. 定期更新 Docker 镜像到最新版本
4. 使用 HTTPS 和 SSL 证书保护通信
5. 配置适当的防火墙规则

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这些配置。

## 许可证

MIT License