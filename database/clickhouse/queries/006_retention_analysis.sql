-- 简单留存率分析
WITH
    first_day AS (
        SELECT
            user_id,
            toDate(min(event_time)) as first_visit_date
        FROM web_analytics.web_logs
        GROUP BY user_id
    ),
    daily_activity AS (
        SELECT
            f.user_id,
            f.first_visit_date,
            toDate(w.event_time) as activity_date,
            dateDiff('day', f.first_visit_date, toDate(w.event_time)) as day_diff
        FROM first_day f
        JOIN web_analytics.web_logs w ON f.user_id = w.user_id
        WHERE dateDiff('day', f.first_visit_date, toDate(w.event_time)) <= 7
    )
SELECT
    day_diff,
    COUNT(DISTINCT user_id) as retained_users,
    round(retained_users * 100.0 / COUNT(DISTINCT first_day.user_id), 2) as retention_rate
FROM daily_activity da
RIGHT JOIN first_day fd ON da.user_id = fd.user_id
GROUP BY day_diff
ORDER BY day_diff
FORMAT PrettyCompact;
