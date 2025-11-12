#!/bin/bash

# Docker 环境启动脚本
# 用法: ./start.sh [environment] [action]

set -e

ENVIRONMENT=$1
ACTION=${2:-up}

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
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

# 检查 Docker 是否运行
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker 未运行，请先启动 Docker"
        exit 1
    fi
}

# 检查 Docker Compose 是否可用
check_docker_compose() {
    if ! command -v docker-compose > /dev/null 2>&1; then
        print_error "Docker Compose 未安装"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo "Docker 环境启动脚本"
    echo ""
    echo "用法: $0 [environment] [action]"
    echo ""
    echo "环境:"
    echo "  base         基础数据服务环境 (默认)"
    echo "  web          Web 开发环境"
    echo "  analysis     数据分析环境"
    echo ""
    echo "动作:"
    echo "  up           启动环境 (默认)"
    echo "  down         停止环境"
    echo "  restart      重启环境"
    echo "  status       查看状态"
    echo "  logs         查看日志"
    echo ""
    echo "示例:"
    echo "  $0 base up           # 启动基础环境"
    echo "  $0 web restart       # 重启 Web 开发环境"
    echo "  $0 analysis logs     # 查看数据分析环境日志"
}

# 启动环境
start_environment() {
    local env_file=$1
    local env_name=$2

    print_info "启动 $env_name 环境..."

    # 创建必要的目录
    mkdir -p data/{mysql,postgres,mongo,clickhouse_new,redis,zookeeper,kafka,etcd,nats}
    mkdir -p data/{web-mysql,web-redis,elasticsearch,rabbitmq,prometheus,grafana,loki,portainer}
    mkdir -p data/{postgres-warehouse,clickhouse-analytics,mongo-analytics,minio,redis,grafana,dbeaver}
    mkdir -p notebooks r-projects sql init clickhouse/{config,users} mongo init

    # 启动服务
    if docker-compose -f "$env_file" up -d; then
        print_success "$env_name 环境启动成功"

        # 显示访问信息
        echo ""
        print_info "服务访问信息:"
        show_access_info "$env_name"
    else
        print_error "$env_name 环境启动失败"
        exit 1
    fi
}

# 停止环境
stop_environment() {
    local env_file=$1
    local env_name=$2

    print_info "停止 $env_name 环境..."

    if docker-compose -f "$env_file" down; then
        print_success "$env_name 环境已停止"
    else
        print_error "$env_name 环境停止失败"
        exit 1
    fi
}

# 重启环境
restart_environment() {
    local env_file=$1
    local env_name=$2

    print_info "重启 $env_name 环境..."
    stop_environment "$env_file" "$env_name"
    start_environment "$env_file" "$env_name"
}

# 显示状态
show_status() {
    local env_file=$1
    local env_name=$2

    print_info "$env_name 环境状态:"
    docker-compose -f "$env_file" ps
}

# 显示日志
show_logs() {
    local env_file=$1
    local env_name=$2
    local service=$3

    if [ -n "$service" ]; then
        print_info "显示 $env_name 环境中 $service 服务的日志:"
        docker-compose -f "$env_file" logs -f "$service"
    else
        print_info "显示 $env_name 环境的所有日志:"
        docker-compose -f "$env_file" logs -f
    fi
}

# 显示访问信息
show_access_info() {
    local env_name=$1

    case $env_name in
        "基础数据服务")
            echo "  MySQL:      localhost:3306 (devuser/devpass)"
            echo "  PostgreSQL: localhost:5432 (devuser/devpass)"
            echo "  MongoDB:    localhost:27017 (devuser/devpass)"
            echo "  ClickHouse: localhost:8123 (devuser/devpass)"
            echo "  Redis:      localhost:6379 (devpass)"
            echo "  Kafka:      localhost:9092"
            ;;
        "Web 开发")
            echo "  Node.js 应用:   http://localhost:3000"
            echo "  Nginx 开发:     http://localhost:8080"
            echo "  API 网关:       http://localhost"
            echo "  MySQL:          localhost:3306 (webuser/webpass123)"
            echo "  Redis:          localhost:6379 (webredis123)"
            echo "  Elasticsearch:  http://localhost:9200"
            echo "  RabbitMQ:       http://localhost:15672 (webadmin/webadmin123)"
            echo "  Prometheus:     http://localhost:9090"
            echo "  Grafana:        http://localhost:3001 (admin/admin123)"
            echo "  Portainer:      https://localhost:9443 (admin/admin123)"
            ;;
        "数据分析")
            echo "  Jupyter:        http://localhost:8888"
            echo "  RStudio:        http://localhost:8787 (rstudio/rstudio123)"
            echo "  PostgreSQL:     localhost:5432 (analyst/analyst123)"
            echo "  ClickHouse:     http://localhost:8123 (analyst/analyst123)"
            echo "  MongoDB:        localhost:27017 (analyst/analyst123)"
            echo "  MinIO:          http://localhost:9001 (analyst/analyst123456)"
            echo "  Airflow:        http://localhost:8080 (airflow/airflow123)"
            echo "  Spark Master:   http://localhost:8081"
            echo "  Superset:       http://localhost:8088 (admin/admin123)"
            echo "  Grafana:        http://localhost:3000 (admin/admin123)"
            echo "  DBeaver:        http://localhost:8978"
            echo "  File Browser:   http://localhost:8082"
            ;;
    esac
}

# 主函数
main() {
    # 检查 Docker 环境
    check_docker
    check_docker_compose

    # 解析参数
    case $ENVIRONMENT in
        "base"|"")
            ENV_FILE="docker-compose.yml"
            ENV_NAME="基础数据服务"
            ;;
        "web")
            ENV_FILE="web-dev.yml"
            ENV_NAME="Web 开发"
            ;;
        "analysis")
            ENV_FILE="data-analysis.yml"
            ENV_NAME="数据分析"
            ;;
        "help"|"-h"|"--help")
            show_help
            exit 0
            ;;
        *)
            print_error "未知环境: $ENVIRONMENT"
            show_help
            exit 1
            ;;
    esac

    # 检查文件是否存在
    if [ ! -f "$ENV_FILE" ]; then
        print_error "找不到环境配置文件: $ENV_FILE"
        exit 1
    fi

    # 执行动作
    case $ACTION in
        "up"|"start")
            start_environment "$ENV_FILE" "$ENV_NAME"
            ;;
        "down"|"stop")
            stop_environment "$ENV_FILE" "$ENV_NAME"
            ;;
        "restart")
            restart_environment "$ENV_FILE" "$ENV_NAME"
            ;;
        "status"|"ps")
            show_status "$ENV_FILE" "$ENV_NAME"
            ;;
        "logs")
            show_logs "$ENV_FILE" "$ENV_NAME" "$3"
            ;;
        *)
            print_error "未知动作: $ACTION"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"