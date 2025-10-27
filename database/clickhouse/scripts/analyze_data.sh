#!/bin/bash

# ClickHouse 数据分析脚本
# 执行各种分析查询并展示结果

set -e

# 配置参数
CLICKHOUSE_CONTAINER="dev-clickhouse"
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

# 执行查询函数
run_query() {
    local query_name="$1"
    local query="$2"

    log_info "$query_name"
    echo "$query" | docker exec -i $CLICKHOUSE_CONTAINER clickhouse-client \
        --query "$(cat)" 2>/dev/null || echo "查询执行失败"
    echo
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