# 快速启动指南

## 一键启动

```bash
# 启动基础数据服务
./start.sh base

# 启动 Web 开发环境
./start.sh web

# 启动数据分析环境
./start.sh analysis
```

## 环境选择

### 基础数据服务
适合：API 开发、微服务测试
- MySQL, PostgreSQL, MongoDB
- Redis, Kafka, etcd
- ClickHouse 列式数据库

### Web 开发环境
适合：Web 应用全栈开发
- Node.js + Nginx
- 完整监控体系 (Prometheus + Grafana)
- 消息队列 (RabbitMQ)
- 搜索引擎 (Elasticsearch)

### 数据分析环境
适合：数据科学、机器学习
- Jupyter Notebook + RStudio
- Spark 集群 + Airflow 工作流
- 多种数据库 (PostgreSQL + ClickHouse + MongoDB)
- 可视化工具 (Superset + Grafana)

## 快速测试

```bash
# 测试基础环境 - 连接 Redis
redis-cli -h localhost -p 6379 -a devpass ping

# 测试 Web 环境 - 访问应用
curl http://localhost:3000

# 测试分析环境 - 访问 Jupyter
curl http://localhost:8888
```

## 常用命令

```bash
# 查看服务状态
./start.sh base status

# 查看日志
./start.sh web logs

# 重启环境
./start.sh analysis restart

# 停止环境
./start.sh base down
```

## 端口速查

| 服务 | 基础环境 | Web 环境 | 分析环境 |
|------|----------|----------|----------|
| MySQL | 3306 | 3306 | - |
| PostgreSQL | 5432 | - | 5432 |
| MongoDB | 27017 | - | 27017 |
| Redis | 6379 | 6379 | 6379 |
| ClickHouse | 8123 | - | 8123 |
| Nginx | - | 8080 | - |
| Grafana | - | 3001 | 3000 |
| Jupyter | - | - | 8888 |
| RStudio | - | - | 8787 |

## 故障排除

1. **端口冲突**: 修改 docker-compose.yml 中的端口映射
2. **内存不足**: 优先启动基础环境，再按需启动其他环境
3. **启动失败**: 检查 Docker 是否运行：`docker info`