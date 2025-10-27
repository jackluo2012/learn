-- 用户统计查询
SELECT
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT session_id) as unique_sessions,
    SUM(is_new_user) as new_users,
    ROUND(new_users * 100.0 / unique_users, 2) as new_user_rate
FROM web_analytics.web_logs
FORMAT PrettyCompact;