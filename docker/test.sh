#!/bin/bash

# Docker 服务连接测试脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 测试连接函数
test_connection() {
    local service=$1
    local test_command=$2
    local success_message=$3

    print_info "测试 $service 连接..."

    if eval "$test_command" > /dev/null 2>&1; then
        print_success "$success_message"
        return 0
    else
        print_error "$service 连接失败"
        return 1
    fi
}

# 等待服务启动
wait_for_service() {
    local service=$1
    local max_attempts=${2:-30}
    local attempt=1

    print_info "等待 $service 服务启动..."

    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps | grep -q "$service.*Up"; then
            print_success "$service 服务已启动"
            return 0
        fi
        print_info "等待 $service 启动... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done

    print_error "$service 服务启动超时"
    return 1
}

# 主测试函数
run_tests() {
    local environment=$1

    case $environment in
        "base")
            test_base_environment
            ;;
        "web")
            test_web_environment
            ;;
        "analysis")
            test_analysis_environment
            ;;
        *)
            print_error "未知环境: $environment"
            echo "可用环境: base, web, analysis"
            exit 1
            ;;
    esac
}

# 测试基础环境
test_base_environment() {
    print_info "开始测试基础数据服务环境..."

    # 测试 Redis
    if test_connection "Redis" "docker exec dev-redis redis-cli -a devpass ping" "Redis 连接正常 (PONG)"; then
        docker exec dev-redis redis-cli -a devpass set test_key "hello_docker" > /dev/null
        docker exec dev-redis redis-cli -a devpass get test_key
    fi

    # 测试 PostgreSQL
    test_connection "PostgreSQL" "docker exec dev-postgres pg_isready -U devuser" "PostgreSQL 连接正常"

    # 测试 MySQL
    test_connection "MySQL" "docker exec dev-mysql mysqladmin ping -h localhost -u devuser -pdevpass" "MySQL 连接正常"

    # 测试 MongoDB
    test_connection "MongoDB" "docker exec dev-mongo mongosh --eval 'db.adminCommand(\"ping\")' --quiet" "MongoDB 连接正常"

    # 测试 ClickHouse
    test_connection "ClickHouse" "curl -f -s -u devuser:devpass http://localhost:8123/" "ClickHouse 连接正常"

    # 测试 etcd
    test_connection "etcd" "docker exec dev-etcd etcdctl --endpoints=http://localhost:2379 endpoint health" "etcd 连接正常"

    # 测试 NATS
    test_connection "NATS" "curl -f -s http://localhost:8222/varz" "NATS 连接正常"

    # 测试 ZooKeeper
    test_connection "ZooKeeper" "docker exec dev-zookeeper zkCli.sh -server localhost:2181 ls /" "ZooKeeper 连接正常"

    # 测试 Kafka
    if wait_for_service "dev-kafka"; then
        test_connection "Kafka" "docker exec dev-kafka kafka-topics --bootstrap-server localhost:9092 --list" "Kafka 连接正常"
    fi
}

# 测试 Web 开发环境
test_web_environment() {
    print_info "开始测试 Web 开发环境..."

    # 测试 Web Redis
    test_connection "Web Redis" "docker exec web-redis redis-cli -a webredis123 ping" "Web Redis 连接正常"

    # 测试 Web MySQL
    test_connection "Web MySQL" "docker exec web-mysql mysqladmin ping -h localhost -u webuser -pwebpass123" "Web MySQL 连接正常"

    # 测试 Elasticsearch
    test_connection "Elasticsearch" "curl -f -s http://localhost:9200/_cluster/health" "Elasticsearch 连接正常"

    # 测试 RabbitMQ
    test_connection "RabbitMQ" "curl -f -s -u webadmin:webadmin123 http://localhost:15672/api/overview" "RabbitMQ 连接正常"

    # 测试 Prometheus
    test_connection "Prometheus" "curl -f -s http://localhost:9090/api/v1/status/config" "Prometheus 连接正常"

    # 测试 Grafana
    test_connection "Grafana" "curl -f -s http://localhost:3001/api/health" "Grafana 连接正常"
}

# 测试数据分析环境
test_analysis_environment() {
    print_info "开始测试数据分析环境..."

    # 测试分析 Redis
    test_connection "分析 Redis" "docker exec analysis-redis redis-cli -a redis123 ping" "分析 Redis 连接正常"

    # 测试数据仓库 PostgreSQL
    test_connection "数据仓库 PostgreSQL" "docker exec analysis-postgres-warehouse pg_isready -U analyst" "数据仓库 PostgreSQL 连接正常"

    # 测试 ClickHouse Analytics
    test_connection "ClickHouse Analytics" "curl -f -s -u analyst:analyst123 http://localhost:8123/" "ClickHouse Analytics 连接正常"

    # 测试 MongoDB Analytics
    test_connection "MongoDB Analytics" "docker exec analysis-mongo mongosh --eval 'db.adminCommand(\"ping\")' --quiet" "MongoDB Analytics 连接正常"

    # 测试 MinIO
    test_connection "MinIO" "curl -f -s http://localhost:9000/minio/health/live" "MinIO 连接正常"

    # 测试 Jupyter
    test_connection "Jupyter" "curl -f -s http://localhost:8888" "Jupyter 连接正常"

    # 测试 RStudio
    test_connection "RStudio" "curl -f -s http://localhost:8787" "RStudio 连接正常"

    # 测试 Superset
    test_connection "Superset" "curl -f -s http://localhost:8088/health" "Superset 连接正常"

    # 测试 Airflow
    test_connection "Airflow" "curl -f -s http://localhost:8080/health" "Airflow 连接正常"

    # 测试 Grafana
    test_connection "分析 Grafana" "curl -f -s http://localhost:3000/api/health" "分析 Grafana 连接正常"

    # 测试 DBeaver
    test_connection "DBeaver" "curl -f -s http://localhost:8978" "DBeaver 连接正常"

    # 测试 File Browser
    test_connection "File Browser" "curl -f -s http://localhost:8082" "File Browser 连接正常"
}

# 显示帮助
show_help() {
    echo "Docker 服务连接测试脚本"
    echo ""
    echo "用法: $0 [environment]"
    echo ""
    echo "环境:"
    echo "  base      测试基础数据服务环境"
    echo "  web       测试 Web 开发环境"
    echo "  analysis  测试数据分析环境"
    echo ""
    echo "示例:"
    echo "  $0 base         # 测试基础环境"
    echo "  $0 web          # 测试 Web 开发环境"
    echo "  $0 analysis     # 测试数据分析环境"
    echo ""
    echo "注意: 请确保相应的环境已经启动"
}

# 主函数
main() {
    if [ $# -eq 0 ]; then
        show_help
        exit 1
    fi

    # 检查 Docker 是否运行
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker 未运行，请先启动 Docker"
        exit 1
    fi

    # 检查 Docker Compose 文件是否存在
    case $1 in
        "base")
            if [ ! -f "docker-compose.yml" ]; then
                print_error "找不到 docker-compose.yml 文件"
                exit 1
            fi
            ;;
        "web")
            if [ ! -f "web-dev.yml" ]; then
                print_error "找不到 web-dev.yml 文件"
                exit 1
            fi
            ;;
        "analysis")
            if [ ! -f "data-analysis.yml" ]; then
                print_error "找不到 data-analysis.yml 文件"
                exit 1
            fi
            ;;
    esac

    print_info "开始测试环境: $1"
    echo "=================================="

    run_tests "$1"

    echo "=================================="
    print_info "测试完成"
}

# 运行主函数
main "$@"