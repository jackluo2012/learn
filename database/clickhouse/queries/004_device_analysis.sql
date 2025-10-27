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