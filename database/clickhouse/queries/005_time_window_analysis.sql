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
