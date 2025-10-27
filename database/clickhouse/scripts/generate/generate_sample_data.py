#!/usr/bin/env python3
"""
ClickHouse 网站访问日志数据生成器
生成模拟的网站访问数据用于学习
"""

import random
import json
from datetime import datetime, timedelta
from faker import Faker

# 初始化Faker
fake = Faker(['zh_CN', 'en_US'])

# 配置参数
RECORDS_COUNT = 10000  # 生成记录数量
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime.now()

# 网站URL列表
URLS = [
    '/', '/home', '/about', '/products', '/contact',
    '/products/item1', '/products/item2', '/products/item3',
    '/blog', '/blog/post1', '/blog/post2', '/blog/post3',
    '/api/users', '/api/products', '/api/orders',
    '/login', '/register', '/dashboard', '/profile',
    '/search?q=laptop', '/search?q=phone', '/category/electronics',
    '/cart', '/checkout', '/help', '/faq'
]

# HTTP方法分布
HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE']
METHOD_WEIGHTS = [0.8, 0.15, 0.04, 0.01]  # GET占80%，POST占15%等

# 状态码分布
STATUS_CODES = [200, 404, 500, 301, 302, 403]
STATUS_WEIGHTS = [0.85, 0.08, 0.02, 0.02, 0.02, 0.01]

# 设备类型
DEVICE_TYPES = ['Desktop', 'Mobile', 'Tablet']
DEVICE_WEIGHTS = [0.6, 0.35, 0.05]

# 浏览器
BROWSERS = ['Chrome', 'Firefox', 'Safari', 'Edge', 'Opera']
BROWSER_WEIGHTS = [0.65, 0.15, 0.12, 0.07, 0.01]

# 操作系统
OS_LIST = ['Windows', 'macOS', 'Linux', 'Android', 'iOS']
OS_WEIGHTS = [0.4, 0.25, 0.15, 0.15, 0.05]

# 国家代码
COUNTRIES = ['CN', 'US', 'JP', 'UK', 'DE', 'FR', 'CA', 'AU', 'KR', 'SG']

def generate_random_ip():
    """生成随机IP地址"""
    return f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"

def generate_user_agent():
    """生成用户代理字符串"""
    browsers = ['Chrome/120.0', 'Firefox/119.0', 'Safari/17.0', 'Edge/120.0']
    os_list = ['Windows NT 10.0', 'Macintosh', 'X11', 'Android 12', 'iPhone OS 17']

    browser = random.choice(browsers)
    os_name = random.choice(os_list)

    return f"Mozilla/5.0 ({os_name}) AppleWebKit/537.36 (KHTML, like Gecko) {browser} Safari/537.36"

def generate_single_record(record_id):
    """生成单条访问记录"""

    # 生成随机时间
    random_seconds = random.randint(0, int((END_DATE - START_DATE).total_seconds()))
    event_time = START_DATE + timedelta(seconds=random_seconds)

    # 生成用户和会话信息
    user_id = f"user_{random.randint(1, 1000)}"
    session_id = f"session_{random.randint(1, 5000)}"

    # 生成请求信息
    url = random.choice(URLS)
    method = random.choices(HTTP_METHODS, weights=METHOD_WEIGHTS)[0]
    status_code = random.choices(STATUS_CODES, weights=STATUS_WEIGHTS)[0]
    response_time = random.randint(50, 2000)  # 50-2000ms
    response_size = random.randint(1024, 1024000)  # 1KB-1MB

    # 生成用户环境信息
    ip_address = generate_random_ip()
    user_agent = generate_user_agent()
    referer = random.choice(['https://www.google.com', 'https://www.baidu.com',
                            'https://www.bing.com', '', 'https://twitter.com'])

    # 生成地理位置
    country = random.choice(COUNTRIES)
    region = fake.province()
    city = fake.city()

    # 生成设备信息
    device_type = random.choices(DEVICE_TYPES, weights=DEVICE_WEIGHTS)[0]
    browser = random.choices(BROWSERS, weights=BROWSER_WEIGHTS)[0]
    os_name = random.choices(OS_LIST, weights=OS_WEIGHTS)[0]

    # 生成内容类型
    content_types = ['text/html', 'application/json', 'text/css', 'application/javascript',
                    'image/png', 'image/jpeg', 'video/mp4']
    content_type = random.choice(content_types)

    # 生成业务字段
    is_new_user = 1 if random.random() < 0.2 else 0  # 20%新用户
    is_bounce = 1 if random.random() < 0.35 else 0    # 35%跳出率

    return {
        'event_time': event_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
        'user_id': user_id,
        'session_id': session_id,
        'url': url,
        'method': method,
        'status_code': status_code,
        'response_time': response_time,
        'ip_address': ip_address,
        'user_agent': user_agent,
        'referer': referer,
        'country': country,
        'region': region,
        'city': city,
        'device_type': device_type,
        'browser': browser,
        'os': os_name,
        'content_type': content_type,
        'response_size': response_size,
        'is_new_user': is_new_user,
        'is_bounce': is_bounce
    }

def generate_csv_data():
    """生成CSV格式的数据"""

    print(f"正在生成 {RECORDS_COUNT} 条模拟数据...")

    # CSV头部
    headers = [
        'event_time', 'user_id', 'session_id', 'url', 'method', 'status_code',
        'response_time', 'ip_address', 'user_agent', 'referer', 'country',
        'region', 'city', 'device_type', 'browser', 'os', 'content_type',
        'response_size', 'is_new_user', 'is_bounce'
    ]

    csv_lines = [','.join(headers)]  # 添加CSV头部

    # 生成数据行
    for i in range(RECORDS_COUNT):
        if i % 1000 == 0:
            print(f"已生成 {i}/{RECORDS_COUNT} 条记录...")

        record = generate_single_record(i)

        # 转义CSV中的特殊字符
        csv_line = ','.join([
            record['event_time'],
            record['user_id'],
            record['session_id'],
            f'"{record["url"]}"',  # URL可能包含逗号，用引号包围
            record['method'],
            str(record['status_code']),
            str(record['response_time']),
            record['ip_address'],
            f'"{record["user_agent"]}"',  # User Agent包含逗号
            f'"{record["referer"]}"',
            record['country'],
            f'"{record["region"]}"',
            f'"{record["city"]}"',
            record['device_type'],
            record['browser'],
            record['os'],
            record['content_type'],
            str(record['response_size']),
            str(record['is_new_user']),
            str(record['is_bounce'])
        ])

        csv_lines.append(csv_line)

    return '\n'.join(csv_lines)

def main():
    """主函数"""
    print("=== ClickHouse 网站访问日志数据生成器 ===")

    # 生成CSV数据
    csv_data = generate_csv_data()

    # 保存到文件
    output_file = '../data/sample/web_logs_sample.csv'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(csv_data)

    print(f"\n✅ 数据生成完成！")
    print(f"📁 文件保存至: {output_file}")
    print(f"📊 总记录数: {RECORDS_COUNT}")
    print(f"📅 时间范围: {START_DATE.strftime('%Y-%m-%d')} ~ {END_DATE.strftime('%Y-%m-%d')}")

    # 显示统计信息
    print(f"\n📈 数据分布预览:")
    print(f"   - 独立用户数: ~1000")
    print(f"   - 独立会话数: ~5000")
    print(f"   - 不同页面数: {len(URLS)}")
    print(f"   - 覆盖国家数: {len(COUNTRIES)}")
    print(f"   - 新用户比例: 20%")
    print(f"   - 跳出率: 35%")

if __name__ == "__main__":
    main()