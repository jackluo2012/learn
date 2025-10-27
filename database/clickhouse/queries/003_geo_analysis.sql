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