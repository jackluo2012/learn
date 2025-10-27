-- 网站访问漏斗分析
SELECT
    level,
    url_pattern,
    COUNT(DISTINCT user_id) as users,
    round(
        users * 100.0 / anyLast (prev_users),
        2
    ) as conversion_rate
FROM (
        SELECT
            user_id, CASE
                WHEN url = '/' THEN 1
                WHEN url LIKE '/products%' THEN 2
                WHEN url LIKE '/login%' THEN 3
                WHEN url LIKE '/dashboard%' THEN 4
                ELSE 5
            END as level, CASE
                WHEN url = '/' THEN '首页'
                WHEN url LIKE '/products%' THEN '产品页'
                WHEN url LIKE '/login%' THEN '登录页'
                WHEN url LIKE '/dashboard%' THEN '仪表板'
                ELSE '其他'
            END as url_pattern, countIf (user_id, level = 1) OVER (
                PARTITION BY
                    user_id
                ORDER BY level
            ) as prev_users
        FROM web_analytics.web_logs
    )
GROUP BY
    level,
    url_pattern
ORDER BY level FORMAT PrettyCompact;