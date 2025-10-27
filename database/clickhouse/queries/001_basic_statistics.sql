-- ClickHouse 基础统计分析查询
-- 展示网站访问日志的基本统计信息

-- 1. 基础访问统计
SELECT '总访问量' as metric, CAST(COUNT(*) AS Float64) as value
FROM web_analytics.web_logs
UNION ALL
SELECT '独立用户数', CAST(
        COUNT(DISTINCT user_id) AS Float64
    )
FROM web_analytics.web_logs
UNION ALL
SELECT '独立会话数', CAST(
        COUNT(DISTINCT session_id) AS Float64
    )
FROM web_analytics.web_logs
UNION ALL
SELECT '平均响应时间(ms)', ROUND(AVG(response_time), 2)
FROM web_analytics.web_logs
UNION ALL
SELECT '成功率(%)', ROUND(
        COUNTIf (status_code < 400) * 100.0 / COUNT(*), 2
    )
FROM web_analytics.web_logs FORMAT PrettyCompact;