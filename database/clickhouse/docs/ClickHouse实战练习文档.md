# 🎯 ClickHouse 实战练习文档

## 📋 前置要求

确保你的系统已安装：
- Docker 和 Docker Compose
- Python 3.x
- curl 工具

## 🚀 第一步：环境准备和ClickHouse部署

### 1.1 检查Docker环境

```bash
# 检查Docker是否运行
docker --version
docker-compose --version

# 检查Docker服务状态
docker ps
```

### 1.2 启动ClickHouse容器

```bash
# 直接运行ClickHouse容器（最简单的方式）
docker run -d \
  --name clickhouse-test \
  -p 8123:8123 \
  -p 9000:9000 \
  -e CLICKHOUSE_USER=devuser \
  -e CLICKHOUSE_PASSWORD=devpass \
  -e CLICKHOUSE_DB=devdb \
  clickhouse/clickhouse-server:23
```

### 1.3 验证ClickHouse启动

```bash
# 等待容器启动完成
sleep 10

# 检查容器状态
docker ps | grep clickhouse

# 测试HTTP接口连接
curl -s "http://localhost:8123/ping"
# 应该返回: Ok.

# 测试数据库连接
docker exec dev-clickhouse clickhouse-client --query "SELECT version()"
# 应该返回版本号，如: 23.8.16.16
```

### 1.4 创建项目目录结构

```bash
# 创建项目主目录
mkdir -p /home/jackluo/learn/database/clickhouse
cd /home/jackluo/learn/database/clickhouse

# 创建目录结构
mkdir -p {sql,data/sample,scripts/{generate,import},queries,docs}

# 验证目录结构
tree -L 3
```

## 🏗️ 第二步：数据库和表结构创建

### 2.1 创建数据库

```bash
# 创建SQL文件
cat > sql/001_create_database.sql << 'EOF'
-- 创建分析数据库
CREATE DATABASE IF NOT EXISTS web_analytics;

-- 使用数据库
USE web_analytics;

-- 显示所有数据库
SHOW DATABASES;
EOF

# 执行SQL脚本
docker exec dev-clickhouse clickhouse-client --query "CREATE DATABASE IF NOT EXISTS web_analytics"

# 验证数据库创建
docker exec dev-clickhouse clickhouse-client --query "SHOW DATABASES"
# 应该能看到 web_analytics 数据库
```

### 2.2 创建网站访问日志表

```bash
# 创建表结构SQL文件
cat > sql/002_create_web_logs_table.sql << 'EOF'
-- 创建网站访问日志表
-- 使用MergeTree引擎，按日期分区，适合时间序列数据分析

CREATE TABLE web_analytics.web_logs (
    -- 主键和时间戳
    event_time DateTime64(3) COMMENT '事件时间，精确到毫秒',

    -- 用户信息
    user_id String COMMENT '用户唯一标识',
    session_id String COMMENT '会话ID',

    -- 请求信息
    url String COMMENT '访问的URL',
    method LowCardinality(String) COMMENT 'HTTP方法',
    status_code UInt16 COMMENT 'HTTP状态码',
    response_time UInt32 COMMENT '响应时间(毫秒)',

    -- 用户环境
    ip_address IPv4 COMMENT '用户IP地址',
    user_agent String COMMENT '用户代理',
    referer String COMMENT '来源页面',

    -- 地理位置
    country FixedString(2) COMMENT '国家代码',
    region FixedString(50) COMMENT '地区',
    city FixedString(50) COMMENT '城市',

    -- 设备信息
    device_type LowCardinality(String) COMMENT '设备类型',
    browser LowCardinality(String) COMMENT '浏览器',
    os LowCardinality(String) COMMENT '操作系统',

    -- 内容信息
    content_type LowCardinality(String) COMMENT '内容类型',
    response_size UInt64 COMMENT '响应大小(字节)',

    -- 业务字段
    is_new_user UInt8 DEFAULT 0 COMMENT '是否新用户',
    is_bounce UInt8 DEFAULT 0 COMMENT '是否跳出访问',

    -- 索引字段
    date Date MATERIALIZED toDate(event_time) COMMENT '日期(物化字段)',
    hour UInt8 MATERIALIZED toHour(event_time) COMMENT '小时(物化字段)'
)
ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(event_time)  -- 按日期分区
ORDER BY (event_time, url, user_id)  -- 排序键，影响查询性能
PRIMARY KEY (event_time)             -- 主键
SETTINGS index_granularity = 8192;   -- 索引粒度
EOF

# 执行建表脚本
docker exec dev-clickhouse clickhouse-client --query "$(cat sql/002_create_web_logs_table.sql)"

# 验证表创建成功
docker exec dev-clickhouse clickhouse-client --query "SHOW TABLES FROM web_analytics"
# 应该能看到: web_logs

# 查看表结构详情
docker exec dev-clickhouse clickhouse-client --query "DESCRIBE web_analytics.web_logs"
```

## 📝 第三步：数据生成脚本

### 3.1 创建数据生成脚本

```bash
# 创建Python数据生成脚本
cat > scripts/generate/generate_simple_data.py << 'EOF'
#!/usr/bin/env python3
"""
ClickHouse 网站访问日志数据生成器 (简化版)
不依赖外部库，生成模拟的网站访问数据用于学习
"""

import random
import json
from datetime import datetime, timedelta

# 配置参数
RECORDS_COUNT = 5000  # 生成记录数量
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime.now()

# 网站URL列表
URLS = [
    '/', '/home', '/about', '/products', '/contact',
    '/products/item1', '/products/item2', '/products/item3',
    '/blog', '/blog/post1', '/blog/post2', '/blog/post3',
    '/api/users', '/api/products', '/api/orders',
    '/login', '/register', '/dashboard', '/profile',
    '/search?q=laptop', '/search?q=phone', '/category/electronics',
    '/cart', '/checkout', '/help', '/faq'
]

# HTTP方法分布
HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE']
METHOD_WEIGHTS = [0.8, 0.15, 0.04, 0.01]

# 状态码分布
STATUS_CODES = [200, 404, 500, 301, 302, 403]
STATUS_WEIGHTS = [0.85, 0.08, 0.02, 0.02, 0.02, 0.01]

# 设备类型
DEVICE_TYPES = ['Desktop', 'Mobile', 'Tablet']
DEVICE_WEIGHTS = [0.6, 0.35, 0.05]

# 浏览器
BROWSERS = ['Chrome', 'Firefox', 'Safari', 'Edge', 'Opera']
BROWSER_WEIGHTS = [0.65, 0.15, 0.12, 0.07, 0.01]

# 操作系统
OS_LIST = ['Windows', 'macOS', 'Linux', 'Android', 'iOS']
OS_WEIGHTS = [0.4, 0.25, 0.15, 0.15, 0.05]

# 国家代码和对应地区
COUNTRY_DATA = [
    ('CN', '北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安', '南京'),
    ('US', 'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia'),
    ('JP', 'Tokyo', 'Osaka', 'Kyoto', 'Yokohama', 'Nagoya'),
    ('UK', 'London', 'Manchester', 'Birmingham', 'Liverpool', 'Edinburgh'),
    ('DE', 'Berlin', 'Munich', 'Hamburg', 'Frankfurt', 'Cologne'),
    ('FR', 'Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice'),
    ('CA', 'Toronto', 'Montreal', 'Vancouver', 'Calgary', 'Ottawa'),
    ('AU', 'Sydney', 'Melbourne', 'Brisbane', 'Perth', 'Adelaide'),
    ('KR', 'Seoul', 'Busan', 'Incheon', 'Daegu', 'Daejeon'),
    ('SG', 'Singapore')
]

def generate_random_ip():
    """生成随机IP地址"""
    return f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"

def generate_user_agent():
    """生成用户代理字符串"""
    browsers = ['Chrome/120.0', 'Firefox/119.0', 'Safari/17.0', 'Edge/120.0']
    os_list = ['Windows NT 10.0', 'Macintosh', 'X11', 'Android 12', 'iPhone OS 17']

    browser = random.choice(browsers)
    os_name = random.choice(os_list)

    return f"Mozilla/5.0 ({os_name}) AppleWebKit/537.36 (KHTML, like Gecko) {browser} Safari/537.36"

def generate_location():
    """生成地理位置信息"""
    country_data = random.choice(COUNTRY_DATA)
    country = country_data[0]
    cities = country_data[1:]
    region = random.choice(cities)
    city = region  # 简化处理，城市和地区相同
    return country, region, city

def generate_single_record(record_id):
    """生成单条访问记录"""

    # 生成随机时间
    random_seconds = random.randint(0, int((END_DATE - START_DATE).total_seconds()))
    event_time = START_DATE + timedelta(seconds=random_seconds)

    # 生成用户和会话信息
    user_id = f"user_{random.randint(1, 1000)}"
    session_id = f"session_{random.randint(1, 5000)}"

    # 生成请求信息
    url = random.choice(URLS)
    method = random.choices(HTTP_METHODS, weights=METHOD_WEIGHTS)[0]
    status_code = random.choices(STATUS_CODES, weights=STATUS_WEIGHTS)[0]
    response_time = random.randint(50, 2000)  # 50-2000ms
    response_size = random.randint(1024, 1024000)  # 1KB-1MB

    # 生成用户环境信息
    ip_address = generate_random_ip()
    user_agent = generate_user_agent()
    referer = random.choice(['https://www.google.com', 'https://www.baidu.com',
                            'https://www.bing.com', '', 'https://twitter.com'])

    # 生成地理位置
    country, region, city = generate_location()

    # 生成设备信息
    device_type = random.choices(DEVICE_TYPES, weights=DEVICE_WEIGHTS)[0]
    browser = random.choices(BROWSERS, weights=BROWSER_WEIGHTS)[0]
    os_name = random.choices(OS_LIST, weights=OS_WEIGHTS)[0]

    # 生成内容类型
    content_types = ['text/html', 'application/json', 'text/css', 'application/javascript',
                    'image/png', 'image/jpeg', 'video/mp4']
    content_type = random.choice(content_types)

    # 生成业务字段
    is_new_user = 1 if random.random() < 0.2 else 0  # 20%新用户
    is_bounce = 1 if random.random() < 0.35 else 0    # 35%跳出率

    return {
        'event_time': event_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
        'user_id': user_id,
        'session_id': session_id,
        'url': url,
        'method': method,
        'status_code': status_code,
        'response_time': response_time,
        'ip_address': ip_address,
        'user_agent': user_agent,
        'referer': referer,
        'country': country,
        'region': region,
        'city': city,
        'device_type': device_type,
        'browser': browser,
        'os': os_name,
        'content_type': content_type,
        'response_size': response_size,
        'is_new_user': is_new_user,
        'is_bounce': is_bounce
    }

def generate_csv_data():
    """生成CSV格式的数据"""

    print(f"正在生成 {RECORDS_COUNT} 条模拟数据...")

    # CSV头部
    headers = [
        'event_time', 'user_id', 'session_id', 'url', 'method', 'status_code',
        'response_time', 'ip_address', 'user_agent', 'referer', 'country',
        'region', 'city', 'device_type', 'browser', 'os', 'content_type',
        'response_size', 'is_new_user', 'is_bounce'
    ]

    csv_lines = [','.join(headers)]  # 添加CSV头部

    # 生成数据行
    for i in range(RECORDS_COUNT):
        if i % 1000 == 0:
            print(f"已生成 {i}/{RECORDS_COUNT} 条记录...")

        record = generate_single_record(i)

        # 转义CSV中的特殊字符
        csv_line = ','.join([
            record['event_time'],
            record['user_id'],
            record['session_id'],
            f'"{record["url"]}"',  # URL可能包含逗号，用引号包围
            record['method'],
            str(record['status_code']),
            str(record['response_time']),
            record['ip_address'],
            f'"{record["user_agent"]}"',  # User Agent包含逗号
            f'"{record["referer"]}"',
            record['country'],
            f'"{record["region"]}"',
            f'"{record["city"]}"',
            record['device_type'],
            record['browser'],
            record['os'],
            record['content_type'],
            str(record['response_size']),
            str(record['is_new_user']),
            str(record['is_bounce'])
        ])

        csv_lines.append(csv_line)

    return '\n'.join(csv_lines)

def main():
    """主函数"""
    print("=== ClickHouse 网站访问日志数据生成器 ===")

    # 生成CSV数据
    csv_data = generate_csv_data()

    # 保存CSV文件
    output_file = '../../data/sample/web_logs_sample.csv'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(csv_data)

    print(f"\n✅ 数据生成完成！")
    print(f"📁 文件保存至: {output_file}")
    print(f"📊 总记录数: {RECORDS_COUNT}")
    print(f"📅 时间范围: {START_DATE.strftime('%Y-%m-%d')} ~ {END_DATE.strftime('%Y-%m-%d')}")

    # 显示统计信息
    print(f"\n📈 数据分布预览:")
    print(f"   - 独立用户数: ~1000")
    print(f"   - 独立会话数: ~5000")
    print(f"   - 不同页面数: {len(URLS)}")
    print(f"   - 覆盖国家数: {len(COUNTRY_DATA)}")
    print(f"   - 新用户比例: 20%")
    print(f"   - 跳出率: 35%")

if __name__ == "__main__":
    main()
EOF

# 给脚本添加执行权限
chmod +x scripts/generate/generate_simple_data.py
```

### 3.2 运行数据生成脚本

```bash
# 进入生成脚本目录
cd scripts/generate

# 运行数据生成脚本
python3 generate_simple_data.py

# 预期输出：
# === ClickHouse 网站访问日志数据生成器 ===
# 正在生成 5000 条模拟数据...
# 已生成 0/5000 条记录...
# 已生成 1000/5000 条记录...
# ...
# ✅ 数据生成完成！
# 📁 文件保存至: ../../data/sample/web_logs_sample.csv
# 📊 总记录数: 5000

# 验证生成的文件
ls -la ../../data/sample/
wc -l ../../data/sample/web_logs_sample.csv

# 查看文件前几行
head -5 ../../data/sample/web_logs_sample.csv
```

## 📥 第四步：数据导入

### 4.1 创建示例数据（快速测试）

```bash
# 回到项目根目录
cd /home/jackluo/learn/database/clickhouse

# 创建少量示例数据用于快速测试
cat > sql/003_insert_sample_data.sql << 'EOF'
-- 插入示例数据
INSERT INTO web_analytics.web_logs VALUES
('2024-01-15 10:30:00.000', 'user_001', 'session_001', '/', 'GET', 200, 150, '192.168.1.1', 'Mozilla/5.0 (Windows NT 10.0) Chrome/120.0', 'https://www.google.com', 'CN', '北京', '北京', 'Desktop', 'Chrome', 'Windows', 'text/html', 10240, 1, 0),
('2024-01-15 10:31:00.000', 'user_001', 'session_001', '/products', 'GET', 200, 200, '192.168.1.1', 'Mozilla/5.0 (Windows NT 10.0) Chrome/120.0', 'https://example.com/', 'CN', '北京', '北京', 'Desktop', 'Chrome', 'Windows', 'text/html', 15360, 0, 0),
('2024-01-15 10:32:00.000', 'user_002', 'session_002', '/login', 'GET', 200, 100, '192.168.1.2', 'Mozilla/5.0 (iPhone OS 17) Safari/17.0', 'https://www.baidu.com', 'US', 'New York', 'New York', 'Mobile', 'Safari', 'iOS', 'text/html', 8192, 1, 0),
('2024-01-15 10:33:00.000', 'user_002', 'session_002', '/api/login', 'POST', 200, 500, '192.168.1.2', 'Mozilla/5.0 (iPhone OS 17) Safari/17.0', 'https://example.com/login', 'US', 'New York', 'New York', 'Mobile', 'Safari', 'iOS', 'application/json', 512, 0, 0),
('2024-01-15 10:34:00.000', 'user_003', 'session_003', '/products/item1', 'GET', 404, 80, '192.168.1.3', 'Mozilla/5.0 (Macintosh) Firefox/119.0', 'https://www.bing.com', 'JP', 'Tokyo', 'Tokyo', 'Desktop', 'Firefox', 'macOS', 'text/html', 2048, 1, 1);
EOF

# 执行数据插入
docker exec dev-clickhouse clickhouse-client --query "$(cat sql/003_insert_sample_data.sql)"

# 验证数据插入
docker exec dev-clickhouse clickhouse-client --query "SELECT COUNT(*) FROM web_analytics.web_logs"
# 应该返回: 5
```

### 4.2 导入大量CSV数据（可选）

```bash
# 创建导入脚本
cat > scripts/import/import_data.sh << 'EOF'
#!/bin/bash

# ClickHouse CSV数据导入脚本
set -e

CLICKHOUSE_CONTAINER="clickhouse-test"
DATABASE="web_analytics"
TABLE="web_logs"
CSV_FILE="../../data/sample/web_logs_sample.csv"

echo "=== ClickHouse CSV数据导入工具 ==="

# 检查文件是否存在
if [ ! -f "$CSV_FILE" ]; then
    echo "错误: 数据文件 '$CSV_FILE' 不存在！"
    echo "请先运行数据生成脚本"
    exit 1
fi

echo "数据文件存在，开始导入..."

# 跳过头部导入数据
tail -n +2 "$CSV_FILE" | docker exec -i $CLICKHOUSE_CONTAINER clickhouse-client \
    --query "INSERT INTO $DATABASE.$TABLE FORMAT CSV"

# 验证导入结果
total_records=$(docker exec $CLICKHOUSE_CONTAINER clickhouse-client \
    --query "SELECT COUNT(*) FROM $DATABASE.$TABLE" 2>/dev/null)

echo "✅ 数据导入完成！"
echo "📊 总记录数: $total_records"
EOF

# 添加执行权限
chmod +x scripts/import/import_data.sh

# 运行导入脚本
cd scripts/import
./import_data.sh
```

## 📊 第五步：查询分析练习

### 5.1 基础统计查询

```bash
# 回到项目根目录
cd /home/jackluo/learn/database/clickhouse

# 创建基础统计查询
cat > queries/001_basic_stats.sql << 'EOF'
-- 基础访问统计
SELECT COUNT(*) as total_visits FROM web_analytics.web_logs;
EOF

# 执行查询
docker exec dev-clickhouse clickhouse-client --query "$(cat queries/001_basic_statistics.sql)"
```

### 5.2 用户统计查询

```bash
# 创建用户统计查询
cat > queries/002_user_stats.sql << 'EOF'
-- 用户统计查询
SELECT
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT session_id) as unique_sessions,
    SUM(is_new_user) as new_users,
    ROUND(new_users * 100.0 / unique_users, 2) as new_user_rate
FROM web_analytics.web_logs
FORMAT PrettyCompact;
EOF

# 执行查询
docker exec dev-clickhouse clickhouse-client --query "$(cat queries/002_user_stats.sql)"
```

### 5.3 地理分析查询

```bash
# 创建地理分析查询
cat > queries/003_geo_analysis.sql << 'EOF'
-- 地理位置分析
SELECT
    country,
    COUNT(*) as visits,
    COUNT(DISTINCT user_id) as unique_users,
    ROUND(AVG(response_time), 2) as avg_response_time
FROM web_analytics.web_logs
GROUP BY country
ORDER BY visits DESC
FORMAT PrettyCompact;
EOF

# 执行查询
docker exec dev-clickhouse clickhouse-client --query "$(cat queries/003_geo_analysis.sql)"
```

### 5.4 设备分析查询

```bash
# 创建设备分析查询
cat > queries/004_device_analysis.sql << 'EOF'
-- 设备和浏览器分析
SELECT
    device_type,
    browser,
    os,
    COUNT(*) as visits,
    COUNT(DISTINCT user_id) as unique_users
FROM web_analytics.web_logs
GROUP BY device_type, browser, os
ORDER BY visits DESC
FORMAT PrettyCompact;
EOF

# 执行查询
docker exec dev-clickhouse clickhouse-client --query "$(cat queries/004_device_analysis.sql)"
```

### 5.5 查看表数据

```bash
# 查看所有数据
docker exec dev-clickhouse clickhouse-client --query "SELECT * FROM web_analytics.web_logs FORMAT PrettyCompact"

# 查看最新几条记录
docker exec dev-clickhouse clickhouse-client --query "SELECT * FROM web_analytics.web_logs ORDER BY event_time DESC LIMIT 3 FORMAT PrettyCompact"
```

## 🛠️ 第六步：创建自动化分析脚本

### 6.1 创建综合分析脚本

```bash
# 创建自动化分析脚本
cat > scripts/analyze_data.sh << 'EOF'
#!/bin/bash

# ClickHouse 数据分析脚本
set -e

CLICKHOUSE_CONTAINER="clickhouse-test"
DATABASE="web_analytics"

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

log_success() {
    echo -e "${GREEN}$1${NC}"
}

# 检查容器状态
check_container() {
    if ! docker ps | grep -q $CLICKHOUSE_CONTAINER; then
        echo "错误: ClickHouse容器未运行！"
        exit 1
    fi
}

# 主分析函数
main() {
    echo "🌐 ClickHouse 网站访问数据分析报告"
    echo "===================================="
    echo

    check_container

    # 1. 基础统计
    log_info "📊 基础访问统计"
    docker exec $CLICKHOUSE_CONTAINER clickhouse-client --query "
        SELECT
            '总访问量' as metric,
            COUNT(*) as value
        FROM $DATABASE.web_logs

        UNION ALL

        SELECT
            '独立用户数',
            COUNT(DISTINCT user_id)
        FROM $DATABASE.web_logs

        UNION ALL

        SELECT
            '独立会话数',
            COUNT(DISTINCT session_id)
        FROM $DATABASE.web_logs

        UNION ALL

        SELECT
            '新用户数',
            SUM(is_new_user)
        FROM $DATABASE.web_logs

        UNION ALL

        SELECT
            '跳出访问数',
            SUM(is_bounce)
        FROM $DATABASE.web_logs

        FORMAT PrettyCompact
    "
    echo

    # 2. 地理分布
    log_info "🌍 地理位置分布"
    docker exec $CLICKHOUSE_CONTAINER clickhouse-client --query "
        SELECT
            country,
            COUNT(*) as visits,
            COUNT(DISTINCT user_id) as unique_users,
            ROUND(AVG(response_time), 2) as avg_response_time_ms
        FROM $DATABASE.web_logs
        GROUP BY country
        ORDER BY visits DESC
        FORMAT PrettyCompact
    "
    echo

    # 3. 设备分析
    log_info "📱 设备和浏览器分析"
    docker exec $CLICKHOUSE_CONTAINER clickhouse-client --query "
        SELECT
            device_type,
            browser,
            os,
            COUNT(*) as visits,
            COUNT(DISTINCT user_id) as unique_users,
            ROUND(AVG(response_time), 2) as avg_response_time_ms
        FROM $DATABASE.web_logs
        GROUP BY device_type, browser, os
        ORDER BY visits DESC
        FORMAT PrettyCompact
    "
    echo

    # 4. 状态码分析
    log_info "📈 HTTP状态码分析"
    docker exec $CLICKHOUSE_CONTAINER clickhouse-client --query "
        SELECT
            status_code,
            CASE
                WHEN status_code < 300 THEN '成功'
                WHEN status_code < 400 THEN '重定向'
                WHEN status_code < 500 THEN '客户端错误'
                ELSE '服务器错误'
            END as status_type,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM $DATABASE.web_logs), 2) as percentage
        FROM $DATABASE.web_logs
        GROUP BY status_code
        ORDER BY count DESC
        FORMAT PrettyCompact
    "
    echo

    # 5. 响应时间分析
    log_info "⚡ 响应时间分析"
    docker exec $CLICKHOUSE_CONTAINER clickhouse-client --query "
        SELECT
            ROUND(AVG(response_time), 2) as avg_response_time_ms,
            MIN(response_time) as min_response_time_ms,
            MAX(response_time) as max_response_time_ms,
            ROUND(quantile(0.50)(response_time), 2) as median_response_time_ms,
            ROUND(quantile(0.95)(response_time), 2) as p95_response_time_ms
        FROM $DATABASE.web_logs
        FORMAT PrettyCompact
    "
    echo

    # 6. 热门页面
    log_info "🔥 热门访问页面"
    docker exec $CLICKHOUSE_CONTAINER clickhouse-client --query "
        SELECT
            url,
            COUNT(*) as visits,
            COUNT(DISTINCT user_id) as unique_users,
            ROUND(AVG(response_time), 2) as avg_response_time_ms
        FROM $DATABASE.web_logs
        GROUP BY url
        ORDER BY visits DESC
        LIMIT 10
        FORMAT PrettyCompact
    "
    echo

    log_success "✅ 分析完成！"
}

# 运行主函数
main "$@"
EOF

# 添加执行权限
chmod +x scripts/analyze_data.sh
```

### 6.2 运行完整分析

```bash
# 运行完整的分析报告
./scripts/analyze_data.sh
```

## 📚 第七步：深入理解ClickHouse特性

### 7.1 查看分区信息

```bash
# 查看表的分区信息
docker exec dev-clickhouse clickhouse-client --query "
SELECT
    partition,
    count() as rows,
    count() * 100.0 / (SELECT count() FROM web_analytics.web_logs) as percentage
FROM system.parts
WHERE database = 'web_analytics' AND table = 'web_logs' AND active = 1
GROUP BY partition
ORDER BY partition
FORMAT PrettyCompact"
```

### 7.2 查看数据压缩率

```bash
# 查看表的压缩信息
docker exec dev-clickhouse clickhouse-client --query "
SELECT
    database,
    table,
    formatReadableSize(sum(bytes)) as table_size,
    formatReadableSize(sum(data_compressed_bytes)) as compressed_size,
    formatReadableSize(sum(data_uncompressed_bytes)) as uncompressed_size,
    round(sum(data_uncompressed_bytes) / sum(data_compressed_bytes), 2) as compression_ratio
FROM system.parts
WHERE database = 'web_analytics' AND table = 'web_logs' AND active = 1
GROUP BY database, table
FORMAT PrettyCompact"
```

### 7.3 测试查询性能

```bash
# 测试不同查询的执行时间
echo "测试查询性能..."

# 简单聚合查询
echo "1. 简单聚合查询:"
time docker exec dev-clickhouse clickhouse-client --query "
SELECT COUNT(*) FROM web_analytics.web_logs WHERE country = 'CN'" > /dev/null

# 复杂分组查询
echo "2. 复杂分组查询:"
time docker exec dev-clickhouse clickhouse-client --query "
SELECT device_type, browser, COUNT(*)
FROM web_analytics.web_logs
GROUP BY device_type, browser
ORDER BY COUNT(*) DESC" > /dev/null

# 时间范围查询
echo "3. 时间范围查询:"
time docker exec dev-clickhouse clickhouse-client --query "
SELECT COUNT(*)
FROM web_analytics.web_logs
WHERE event_time BETWEEN '2024-01-01' AND '2024-12-31'" > /dev/null
```

## 🔍 第八步：高级查询练习

### 8.1 时间窗口分析

```bash
# 创建时间窗口分析查询
cat > queries/005_time_window_analysis.sql << 'EOF'
-- 时间窗口分析
SELECT
    toHour(event_time) as hour,
    COUNT(*) as visits,
    COUNT(DISTINCT user_id) as unique_users,
    ROUND(AVG(response_time), 2) as avg_response_time
FROM web_analytics.web_logs
GROUP BY hour
ORDER BY hour
FORMAT PrettyCompact;
EOF

# 执行查询
docker exec dev-clickhouse clickhouse-client --query "$(cat queries/005_time_window_analysis.sql)"
```

### 8.2 留存率分析

```bash
# 创建留存率分析查询
cat > queries/006_retention_analysis.sql << 'EOF'
-- 简单留存率分析
WITH
    first_day AS (
        SELECT
            user_id,
            toDate(min(event_time)) as first_visit_date
        FROM web_analytics.web_logs
        GROUP BY user_id
    ),
    daily_activity AS (
        SELECT
            f.user_id,
            f.first_visit_date,
            toDate(w.event_time) as activity_date,
            dateDiff('day', f.first_visit_date, toDate(w.event_time)) as day_diff
        FROM first_day f
        JOIN web_analytics.web_logs w ON f.user_id = w.user_id
        WHERE dateDiff('day', f.first_visit_date, toDate(w.event_time)) <= 7
    )
SELECT
    day_diff,
    COUNT(DISTINCT user_id) as retained_users,
    round(retained_users * 100.0 / COUNT(DISTINCT first_day.user_id), 2) as retention_rate
FROM daily_activity da
RIGHT JOIN first_day fd ON da.user_id = fd.user_id
GROUP BY day_diff
ORDER BY day_diff
FORMAT PrettyCompact;
EOF

# 执行查询
docker exec dev-clickhouse clickhouse-client --query "$(cat queries/006_retention_analysis.sql)"
```

### 8.3 漏斗分析

```bash
# 创建漏斗分析查询
cat > queries/007_funnel_analysis.sql << 'EOF'
-- 网站访问漏斗分析
SELECT
    level,
    url_pattern,
    COUNT(DISTINCT user_id) as users,
    round(users * 100.0 / LAG(users) OVER (ORDER BY level), 2) as conversion_rate
FROM (
    SELECT
        user_id,
        CASE
            WHEN url = '/' THEN 1
            WHEN url LIKE '/products%' THEN 2
            WHEN url LIKE '/login%' THEN 3
            WHEN url LIKE '/dashboard%' THEN 4
            ELSE 5
        END as level,
        CASE
            WHEN url = '/' THEN '首页'
            WHEN url LIKE '/products%' THEN '产品页'
            WHEN url LIKE '/login%' THEN '登录页'
            WHEN url LIKE '/dashboard%' THEN '仪表板'
            ELSE '其他'
        END as url_pattern
    FROM web_analytics.web_logs
)
GROUP BY level, url_pattern
ORDER BY level
FORMAT PrettyCompact;
EOF

# 执行查询
docker exec dev-clickhouse clickhouse-client --query "$(cat queries/007_funnel_analysis.sql)"
```

## 🧹 第九步：清理和维护

### 9.1 创建项目文档

```bash
# 创建项目README
cat > README.md << 'EOF'
# 🌐 ClickHouse 实时网站访问分析系统

## 项目概述
基于ClickHouse构建的实时网站访问日志分析系统，用于学习ClickHouse的核心特性和最佳实践。

## 技术栈
- **数据库**: ClickHouse 23.8.16.16
- **连接方式**: HTTP接口 + 客户端工具
- **数据格式**: CSV + JSON
- **脚本语言**: Bash + Python

## 快速开始

### 1. 启动ClickHouse
```bash
docker run -d --name clickhouse-test -p 8123:8123 -p 9000:9000 \
  -e CLICKHOUSE_USER=devuser -e CLICKHOUSE_PASSWORD=devpass \
  clickhouse/clickhouse-server:23
```

### 2. 创建数据库和表
```bash
docker exec dev-clickhouse clickhouse-client --query "CREATE DATABASE web_analytics"
docker exec dev-clickhouse clickhouse-client --query "$(cat sql/002_create_web_logs_table.sql)"
```

### 3. 生成测试数据
```bash
cd scripts/generate && python3 generate_simple_data.py
```

### 4. 插入示例数据
```bash
docker exec dev-clickhouse clickhouse-client --query "$(cat sql/003_insert_sample_data.sql)"
```

### 5. 运行分析
```bash
./scripts/analyze_data.sh
```

## 项目结构
```
clickhouse/
├── sql/           # SQL脚本
├── scripts/       # 工具脚本
├── queries/       # 查询脚本
├── data/sample/   # 示例数据
└── docs/          # 文档
```

## 学习目标
- 掌握ClickHouse数据类型和表引擎
- 理解MergeTree系列引擎的特性
- 学习性能优化技巧
- 实践实时数据处理方案
EOF
```

### 9.2 清理环境（可选）

```bash
# 如果需要清理环境
echo "清理ClickHouse环境..."

# 停止并删除容器
docker stop clickhouse-test
docker rm clickhouse-test

# 删除项目文件（谨慎操作）
# rm -rf /home/jackluo/learn/database/clickhouse

echo "环境清理完成"
```

## 🎯 学习检查点

完成以上所有步骤后，你应该掌握：

✅ **ClickHouse基础操作**
- Docker容器部署
- 数据库和表创建
- 基础SQL查询

✅ **数据建模能力**
- MergeTree引擎配置
- 分区策略设计
- 数据类型选择

✅ **数据处理技能**
- CSV数据导入
- 数据生成和模拟
- 数据验证方法

✅ **分析查询能力**
- 聚合统计查询
- 多维度分析
- 性能优化查询

✅ **自动化脚本**
- Shell脚本编写
- 数据处理流水线
- 自动化报告生成

## 🚀 下一步学习建议

1. **物化视图**: 学习实时聚合预计算
2. **集群部署**: 了解分布式ClickHouse
3. **流式处理**: 集成Kafka实时数据
4. **可视化**: 连接Grafana或Tableau
5. **性能调优**: 深入学习查询优化

恭喜你完成了ClickHouse的实战学习！继续探索更多高级功能吧！
EOF

chmod +x /home/jackluo/learn/database/clickhouse/docs/ClickHouse实战练习文档.md
```

## 📖 文档说明

我已经为你创建了一个完整的练习文档，包含：

1. **详细步骤说明**: 每一步都有具体的命令和预期输出
2. **代码示例**: 所有脚本和SQL都已提供完整代码
3. **验证方法**: 每个步骤都有验证命令确保操作成功
4. **学习要点**: 每个阶段都有学习目标和知识点解释

### 📋 文档位置
```
/home/jackluo/learn/database/clickhouse/docs/ClickHouse实战练习文档.md
```

### 🎯 使用方法
1. 按照文档顺序逐步执行
2. 每个步骤都提供了完整的命令
3. 可以复制粘贴命令直接执行
4. 包含了验证命令确保操作正确

### ⚠️ 注意事项
- 确保Docker环境正常运行
- 按顺序执行，不要跳过步骤
- 遇到错误时检查前面的步骤是否完成
- 文档中提供了清理命令可以重新开始

现在你可以按照这个详细的文档一步一步练习ClickHouse的实战操作了！