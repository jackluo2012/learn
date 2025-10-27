#!/bin/bash

# ClickHouse CSV数据导入脚本
# 用于将生成的CSV数据导入到ClickHouse中

set -e  # 遇到错误时退出

# 配置参数
CLICKHOUSE_CONTAINER="clickhouse-test"
DATABASE="web_analytics"
TABLE="web_logs"
CSV_FILE="../../data/sample/web_logs_sample.csv"
BATCH_SIZE=1000  # 每批次导入的记录数

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
        log_info "请先启动容器: docker start $CLICKHOUSE_CONTAINER"
        exit 1
    fi

    log_success "ClickHouse容器运行正常"
}

# 检查文件是否存在
check_file() {
    log_info "检查数据文件..."

    if [ ! -f "$CSV_FILE" ]; then
        log_error "数据文件 '$CSV_FILE' 不存在！"
        log_info "请先运行数据生成脚本: python3 scripts/generate/generate_simple_data.py"
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
        log_info "请先创建表结构"
        exit 1
    fi

    log_success "表结构检查通过"
}

# 显示数据预览
preview_data() {
    log_info "数据预览（前5行）:"
    echo "----------------------------------------"
    head -5 "$CSV_FILE" | column -t -s ','
    echo "----------------------------------------"
}

# 获取文件行数（不包括头部）
get_record_count() {
    local total_lines=$(wc -l < "$CSV_FILE")
    echo $((total_lines - 1))  # 减去CSV头部行
}

# 导入数据
import_data() {
    log_info "开始导入数据到 $DATABASE.$TABLE"

    local total_records=$(get_record_count)
    log_info "总记录数: $total_records"

    # 记录开始时间
    local start_time=$(date +%s)

    # 检查表中是否已有数据
    local existing_records=$(docker exec $CLICKHOUSE_CONTAINER clickhouse-client \
        --query "SELECT COUNT(*) FROM $DATABASE.$TABLE" 2>/dev/null || echo "0")

    if [ "$existing_records" != "0" ]; then
        log_warning "表中已存在 $existing_records 条记录"
        read -p "是否清空现有数据后重新导入？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "清空现有数据..."
            docker exec $CLICKHOUSE_CONTAINER clickhouse-client \
                --query "TRUNCATE TABLE $DATABASE.$TABLE" 2>/dev/null
            log_success "数据清空完成"
        else
            log_info "追加导入新数据..."
        fi
    fi

    # 复制CSV文件到容器
    log_info "复制数据文件到容器..."
    local container_csv_path="/tmp/web_logs_import.csv"

    docker cp "$CSV_FILE" "$CLICKHOUSE_CONTAINER:$container_csv_path"

    # 执行数据导入
    log_info "执行数据导入..."

    docker exec $CLICKHOUSE_CONTAINER clickhouse-client \
        --query "INSERT INTO $DATABASE.$TABLE FORMAT CSVWithNames" \
        < "$CSV_FILE"

    # 检查导入结果
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local imported_records=$(docker exec $CLICKHOUSE_CONTAINER clickhouse-client \
        --query "SELECT COUNT(*) FROM $DATABASE.$TABLE" 2>/dev/null)

    log_success "数据导入完成！"
    log_info "导入时间: ${duration}秒"
    log_info "导入记录数: $imported_records"

    if [ "$imported_records" -gt "$existing_records" ]; then
        local new_records=$((imported_records - existing_records))
        log_success "新增记录数: $new_records"
    fi

    # 计算导入速度
    if [ "$duration" -gt 0 ]; then
        local records_per_second=$((new_records / duration))
        log_info "导入速度: $records_per_second 记录/秒"
    fi
}

# 验证导入结果
verify_import() {
    log_info "验证导入结果..."

    # 检查数据完整性
    local total_records=$(docker exec $CLICKHOUSE_CONTAINER clickhouse-client \
        --query "SELECT COUNT(*) FROM $DATABASE.$TABLE" 2>/dev/null)

    local distinct_users=$(docker exec $CLICKHOUSE_CONTAINER clickhouse-client \
        --query "SELECT COUNT(DISTINCT user_id) FROM $DATABASE.$TABLE" 2>/dev/null)

    local date_range=$(docker exec $CLICKHOUSE_CONTAINER clickhouse-client \
        --query "SELECT
            MIN(event_time) as min_date,
            MAX(event_time) as max_date
        FROM $DATABASE.$TABLE FORMAT CSV" 2>/dev/null)

    local top_countries=$(docker exec $CLICKHOUSE_CONTAINER clickhouse-client \
        --query "SELECT
            country,
            COUNT(*) as visits
        FROM $DATABASE.$TABLE
        GROUP BY country
        ORDER BY visits DESC
        LIMIT 5 FORMAT CSV" 2>/dev/null)

    echo
    log_success "=== 数据验证报告 ==="
    echo "总记录数: $total_records"
    echo "独立用户数: $distinct_users"
    echo "日期范围: $date_range"
    echo "TOP 5 国家/地区:"
    echo "$top_countries" | while IFS=',' read -r country visits; do
        echo "  $country: $visits 次访问"
    done
    echo "========================"
}

# 显示基础统计
show_basic_stats() {
    log_info "生成基础统计信息..."

    docker exec $CLICKHOUSE_CONTAINER clickhouse-client \
        --query "
        SELECT
            '总访问量' as metric,
            COUNT(*) as value
        FROM $DATABASE.$TABLE

        UNION ALL

        SELECT
            '独立用户数',
            COUNT(DISTINCT user_id)
        FROM $DATABASE.$TABLE

        UNION ALL

        SELECT
            '独立会话数',
            COUNT(DISTINCT session_id)
        FROM $DATABASE.$TABLE

        UNION ALL

        SELECT
            '平均响应时间(ms)',
            ROUND(AVG(response_time), 2)
        FROM $DATABASE.$TABLE

        UNION ALL

        SELECT
            '成功率(%)',
            ROUND(COUNTIf(status_code < 400) * 100.0 / COUNT(*), 2)
        FROM $DATABASE.$TABLE

        FORMAT PrettyCompact
        " 2>/dev/null
}

# 主函数
main() {
    echo "=== ClickHouse CSV数据导入工具 ==="
    echo

    # 执行检查和导入
    check_container
    check_file
    check_table
    preview_data

    # 确认导入
    echo
    read -p "确认开始导入数据？(Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        import_data
        verify_import
        show_basic_stats
        log_success "所有操作完成！"
    else
        log_info "操作已取消"
    fi
}

# 如果直接运行脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi