-- 创建网站访问日志表
-- 使用MergeTree引擎，按日期分区，适合时间序列数据分析

CREATE TABLE web_analytics.web_logs (
    -- 主键和时间戳
    event_time DateTime64(3) COMMENT '事件时间，精确到毫秒',

    -- 用户信息
    user_id String COMMENT '用户唯一标识',
    session_id String COMMENT '会话ID',

    -- 请求信息
    url String COMMENT '访问的URL',
    method LowCardinality(String) COMMENT 'HTTP方法',
    status_code UInt16 COMMENT 'HTTP状态码',
    response_time UInt32 COMMENT '响应时间(毫秒)',

    -- 用户环境
    ip_address IPv4 COMMENT '用户IP地址',
    user_agent String COMMENT '用户代理',
    referer String COMMENT '来源页面',

    -- 地理位置
    country FixedString(2) COMMENT '国家代码',
    region FixedString(50) COMMENT '地区',
    city FixedString(50) COMMENT '城市',

    -- 设备信息
    device_type LowCardinality(String) COMMENT '设备类型',
    browser LowCardinality(String) COMMENT '浏览器',
    os LowCardinality(String) COMMENT '操作系统',

    -- 内容信息
    content_type LowCardinality(String) COMMENT '内容类型',
    response_size UInt64 COMMENT '响应大小(字节)',

    -- 业务字段
    is_new_user UInt8 DEFAULT 0 COMMENT '是否新用户',
    is_bounce UInt8 DEFAULT 0 COMMENT '是否跳出访问',

    -- 索引字段
    date Date MATERIALIZED toDate(event_time) COMMENT '日期(物化字段)',
    hour UInt8 MATERIALIZED toHour(event_time) COMMENT '小时(物化字段)'
)
ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(event_time)  -- 按日期分区
ORDER BY (event_time, url, user_id)  -- 排序键，影响查询性能
PRIMARY KEY (event_time)             -- 主键
SETTINGS index_granularity = 8192;   -- 索引粒度