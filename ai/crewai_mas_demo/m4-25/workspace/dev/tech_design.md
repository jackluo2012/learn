# 技术设计 - 自然语言日程解析模块

## 1. 架构说明

- **系统定位**：本模块属于 NLP 解析工具集，独立运行，无外部服务依赖。
- **模块划分**：核心解析逻辑 + 时间处理工具函数。
- **关键依赖**：
  - Python 标准库（`datetime`, `re`）
  - 自定义异常类 `ParseError`
- **复杂度评估**：中等，主要复杂度在时间表达的多样性。
- **关键风险**：
  - 输入格式不规范可能导致解析失败。
  - 相对时间计算需要基准日期。

## 2. 接口定义

```python
def parse_schedule(text: str, base_date: datetime) -> dict[str, Any]:
    """
    解析自然语言日程描述。

    Args:
        text: 用户输入的中文日程描述。
        base_date: 相对时间的基准日期。

    Returns:
        {
            "title": str,
            "start_time": str,  # ISO 8601 格式
            "end_time": str,
            "location": str,
            "attendees": list[str]
        }

    Raises:
        ParseError: 输入无法解析为有效日程。
    """
```

## 3. 实现要点

- **选型**：正则表达式 + 规则引擎（不使用外部 NLP API）。
- **理由**：验收标准要求 ≤1秒且无网络请求，排除 LLM/API 方案。
- **代价**：无法处理训练数据以外的罕见时间表达，覆盖度约 85%。
- **核心算法伪代码**：
  ```python
  def parse_schedule(text, base_date):
      match = re.match(TIME_PATTERN, text)
      if not match:
          raise ParseError("无法解析输入")

      title = extract_title(text)
      start_time, end_time = calculate_time_range(match, base_date)
      location = extract_location(text)
      attendees = extract_attendees(text)

      return {
          "title": title,
          "start_time": start_time.isoformat(),
          "end_time": end_time.isoformat(),
          "location": location,
          "attendees": attendees
      }
  ```
- **错误处理策略**：所有异常统一抛出 `ParseError`，调用方需捕获。
- **性能约束考量**：通过正则预编译优化匹配速度。

## 4. 单元测试用例

| 用例ID | 用例名称 | 输入 | 期望输出 | 类型 |
|--------|---------|------|---------|------|
| UT-01  | 标准日程解析 | "明天下午3点开会", base_date=datetime(2026,3,26) | {"title": "开会", "start_time": "2026-03-27T15:00:00+08:00", ...} | 正常 |
| UT-02  | 时间范围解析 | "2点到4点代码评审", base_date=datetime(2026,3,26) | {"title": "代码评审", "start_time": "2026-03-26T14:00:00+08:00", ...} | 正常 |
| UT-03  | 相对时间-下周 | "下周一上午10点", base_date=datetime(2026,3,26) | {"title": "", "start_time": "2026-04-06T10:00:00+08:00", ...} | 边界 |
| UT-04  | 无效输入 | "随便说点什么", base_date=datetime(2026,3,26) | ParseError | 异常 |