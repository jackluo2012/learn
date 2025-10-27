#!/bin/bash

# ClickHouse CSV数据导入脚本
# 用于将生成的CSV数据导入到ClickHouse中

set -e  # 遇到错误时退出

# 配置参数
CLICKHOUSE_CONTAINER="dev-clickhouse"
DATABASE="web_analytics"
TABLE="web_logs"
CSV_FILE="../../data/sample/web_logs_sample.csv"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查容器是否运行
check_container() {
    log_info "检查ClickHouse容器状态..."

    if ! docker ps | grep -q $CLICKHOUSE_CONTAINER; then
        log_error "ClickHouse容器 '$CLICKHOUSE_CONTAINER' 未运行！"
        exit 1
    fi

    log_success "ClickHouse容器运行正常"
}

# 检查文件是否存在
check_file() {
    log_info "检查数据文件..."

    if [ ! -f "$CSV_FILE" ]; then
        log_error "数据文件 '$CSV_FILE' 不存在！"
        exit 1
    fi

    local file_size=$(wc -l < "$CSV_FILE")
    log_success "数据文件存在，共 $file_size 行（包括头部）"
}

# 检查表是否存在
check_table() {
    log_info "检查表结构..."

    local table_exists=$(docker exec $CLICKHOUSE_CONTAINER clickhouse-client \
        --query "EXISTS TABLE $DATABASE.$TABLE" 2>/dev/null)

    if [ "$table_exists" != "1" ]; then
        log_error "表 '$DATABASE.$TABLE' 不存在！"
        exit 1
    fi

    log_success "表结构检查通过"
}

# 导入数据
import_data() {
    log_info "开始导入数据到 $DATABASE.$TABLE"

    # 复制CSV文件到容器
    log_info "复制数据文件到容器..."
    local container_csv_path="/tmp/web_logs_import.csv"

    docker cp "$CSV_FILE" "$CLICKHOUSE_CONTAINER:$container_csv_path"

    # 执行数据导入
    log_info "执行数据导入..."

    docker exec $CLICKHOUSE_CONTAINER clickhouse-client \
        --query "INSERT INTO $DATABASE.$TABLE FORMAT CSVWithNames" \
        < "$CSV_FILE"

    log_success "数据导入完成！"
}

# 验证导入结果
verify_import() {
    log_info "验证导入结果..."

    local total_records=$(docker exec $CLICKHOUSE_CONTAINER clickhouse-client \
        --query "SELECT COUNT(*) FROM $DATABASE.$TABLE" 2>/dev/null)

    local distinct_users=$(docker exec $CLICKHOUSE_CONTAINER clickhouse-client \
        --query "SELECT COUNT(DISTINCT user_id) FROM $DATABASE.$TABLE" 2>/dev/null)

    log_success "=== 数据验证报告 ==="
    echo "总记录数: $total_records"
    echo "独立用户数: $distinct_users"
    echo "========================"
}

# 主函数
main() {
    echo "=== ClickHouse CSV数据导入工具 ==="
    echo

    check_container
    check_file
    check_table
    import_data
    verify_import
    log_success "所有操作完成！"
}

# 如果直接运行脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi