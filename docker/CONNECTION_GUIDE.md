# Docker 服务连接指南

## 基础数据服务环境连接方式

### MySQL 数据库
```bash
# 命令行连接
docker exec -it dev-mysql mysql -u devuser -pdevpass -D devdb

# 使用 mysql 客户端
mysql -h localhost -P 3306 -u devuser -pdevpass devdb

# 连接信息
Host: localhost
Port: 3306
Database: devdb
Username: devuser
Password: devpass
Root Password: admin
```

### PostgreSQL 数据库
```bash
# 命令行连接
docker exec -it dev-postgres psql -U devuser -d devdb

# 使用 psql 客户端
psql -h localhost -p 5432 -U devuser -d devdb

# 连接信息
Host: localhost
Port: 5432
Database: devdb
Username: devuser
Password: devpass
```

### MongoDB 数据库
```bash
# 命令行连接
docker exec -it dev-mongo mongosh -u devuser -p devpass --authenticationDatabase admin

# 使用 mongosh 客户端
mongosh "mongodb://devuser:devpass@localhost:27017/admin"

# 连接信息
Host: localhost
Port: 27017
Database: admin (认证)
Username: devuser
Password: devpass
```

### ClickHouse 数据库
```bash
# HTTP 接口
curl -u devuser:devpass "http://localhost:8123/"

# 命令行连接
docker exec -it dev-clickhouse clickhouse-client -u devuser --password devpass

# 连接信息
HTTP Port: 8123
Native Port: 9000
Username: devuser
Password: devpass
Database: devdb
```

### Redis 缓存
```bash
# 命令行连接
docker exec -it dev-redis redis-cli -a devpass

# 使用 redis-cli 客户端
redis-cli -h localhost -p 6379 -a devpass

# 连接信息
Host: localhost
Port: 6379
Password: devpass
```

### Kafka 消息队列
```bash
# 查看主题列表
docker exec -it dev-kafka kafka-topics --bootstrap-server localhost:9092 --list

# 创建主题
docker exec -it dev-kafka kafka-topics --bootstrap-server localhost:9092 --create --topic test-topic --partitions 1 --replication-factor 1

# 生产消息
docker exec -it dev-kafka kafka-console-producer --bootstrap-server localhost:9092 --topic test-topic

# 消费消息
docker exec -it dev-kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic test-topic --from-beginning

# 连接信息
Bootstrap Server: localhost:9092
```

### ZooKeeper
```bash
# 连接 ZooKeeper
docker exec -it dev-zookeeper zkCli.sh -server localhost:2181

# 连接信息
Host: localhost
Port: 2181
```

### etcd 键值存储
```bash
# 命令行操作
docker exec -it dev-etcd etcdctl --endpoints=http://localhost:2379 put key1 value1
docker exec -it dev-etcd etcdctl --endpoints=http://localhost:2379 get key1

# 连接信息
Endpoints: http://localhost:2379
```

### NATS 消息系统
```bash
# 测试连接
curl http://localhost:8222/varz

# 连接信息
Port: 4222 (客户端连接)
Monitor Port: 8222 (监控)
Cluster Port: 6222
```

## Web 开发环境连接方式

### Web 应用 MySQL
```bash
# 连接信息
Host: localhost
Port: 3306
Database: webapp
Username: webuser
Password: webpass123
```

### Web Redis
```bash
# 连接信息
Host: localhost
Port: 6379
Password: webredis123
```

### Elasticsearch
```bash
# HTTP 访问
curl http://localhost:9200

# API 端点
http://localhost:9200/_cluster/health
```

### RabbitMQ
```bash
# Web 管理界面
URL: http://localhost:15672
Username: webadmin
Password: webadmin123

# 连接信息
Host: localhost
Port: 5672
Username: webadmin
Password: webadmin123
```

### Grafana
```bash
# Web 界面
URL: http://localhost:3001
Username: admin
Password: admin123
```

### Portainer
```bash
# Web 界面
URL: https://localhost:9443
Username: admin
Password: admin123
```

## 数据分析环境连接方式

### RStudio
```bash
# Web 界面
URL: http://localhost:8787
Username: rstudio
Password: rstudio123
```

### Jupyter Notebook
```bash
# Web 界面
URL: http://localhost:8888
无需密码（开发环境）
```

### 数据仓库 PostgreSQL
```bash
# 连接信息
Host: localhost
Port: 5432
Database: datawarehouse
Username: analyst
Password: analyst123
```

### ClickHouse Analytics
```bash
# 连接信息
HTTP Port: 8123
Native Port: 9000
MySQL Protocol Port: 9004
PostgreSQL Protocol Port: 9005
Username: analyst
Password: analyst123
Database: analytics
```

### MongoDB Analytics
```bash
# 连接信息
Host: localhost
Port: 27017
Username: analyst
Password: analyst123
```

### MinIO 对象存储
```bash
# Web 管理界面
URL: http://localhost:9001
Username: analyst
Password: analyst123456

# API 端点
Endpoint: http://localhost:9000
```

### Airflow 工作流
```bash
# Web 界面
URL: http://localhost:8080
Username: airflow
Password: airflow123
```

### Superset 数据可视化
```bash
# Web 界面
URL: http://localhost:8088
Username: admin
Password: admin123
```

### DBeaver 数据库管理
```bash
# Web 界面
URL: http://localhost:8978
```

### File Browser 文件管理
```bash
# Web 界面
URL: http://localhost:8082
```

## 容器内调试技巧

### 进入容器
```bash
# 进入 MySQL 容器
docker exec -it dev-mysql bash

# 进入 PostgreSQL 容器
docker exec -it dev-postgres bash

# 进入 MongoDB 容器
docker exec -it dev-mongo bash

# 进入 Redis 容器
docker exec -it dev-redis bash
```

### 查看容器日志
```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs mysql
docker-compose logs -f redis  # 实时日志
```

### 查看容器状态
```bash
# 查看所有容器状态
docker-compose ps

# 查看容器资源使用
docker stats
```

### 容器网络信息
```bash
# 查看网络配置
docker network ls
docker network inspect docker_dev-network

# 容器间连接测试
docker exec -it dev-mysql ping dev-redis
```

## 编程语言连接示例

### Python 连接示例
```python
# MySQL 连接
import pymysql
conn = pymysql.connect(
    host='localhost',
    port=3306,
    user='devuser',
    password='devpass',
    database='devdb'
)

# PostgreSQL 连接
import psycopg2
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    user='devuser',
    password='devpass',
    database='devdb'
)

# MongoDB 连接
from pymongo import MongoClient
client = MongoClient('mongodb://devuser:devpass@localhost:27017/')
db = client.admin

# Redis 连接
import redis
r = redis.Redis(host='localhost', port=6379, password='devpass')
```

### Node.js 连接示例
```javascript
// MySQL 连接
const mysql = require('mysql2');
const conn = mysql.createConnection({
  host: 'localhost',
  port: 3306,
  user: 'devuser',
  password: 'devpass',
  database: 'devdb'
});

// MongoDB 连接
const { MongoClient } = require('mongodb');
const client = new MongoClient('mongodb://devuser:devpass@localhost:27017/');

// Redis 连接
const redis = require('redis');
const client = redis.createClient({
  host: 'localhost',
  port: 6379,
  password: 'devpass'
});
```

### Java 连接示例
```java
// MySQL JDBC 连接
String url = "jdbc:mysql://localhost:3306/devdb";
String user = "devuser";
String password = "devpass";
Connection conn = DriverManager.getConnection(url, user, password);

// PostgreSQL JDBC 连接
String url = "jdbc:postgresql://localhost:5432/devdb";
String user = "devuser";
String password = "devpass";
Connection conn = DriverManager.getConnection(url, user, password);

// Redis Jedis 连接
Jedis jedis = new Jedis("localhost", 6379);
jedis.auth("devpass");
```

## 故障排除

### 常见连接问题

1. **端口被占用**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep :3306

   # 修改 docker-compose.yml 中的端口映射
   ports:
     - "3307:3306"  # 使用不同端口
   ```

2. **权限问题**
   ```bash
   # 检查容器用户权限
   docker exec -it dev-mysql id

   # 重置密码
   docker-compose restart mysql
   ```

3. **网络问题**
   ```bash
   # 检查网络连接
   docker network ls
   docker network inspect docker_dev-network

   # 重建网络
   docker-compose down
   docker network prune
   docker-compose up -d
   ```

4. **容器启动失败**
   ```bash
   # 查看详细错误
   docker-compose logs service_name

   # 重建容器
   docker-compose down -v
   docker-compose up -d
   ```

### 性能优化

1. **内存限制**
   ```yaml
   services:
     mysql:
       mem_limit: 2g
       memswap_limit: 2g
   ```

2. **数据目录优化**
   ```bash
   # 使用 SSD 存储数据库数据
   # 定期清理日志
   docker-compose exec mysql mysql -u root -e "PURGE BINARY LOGS BEFORE DATE_SUB(NOW(), INTERVAL 7 DAY);"
   ```

## 安全建议

1. **更改默认密码**
2. **使用强密码**
3. **限制网络访问**
4. **定期更新镜像**
5. **启用 SSL/TLS**
6. **备份数据**