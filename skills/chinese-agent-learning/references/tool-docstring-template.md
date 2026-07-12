# Tool Docstring 模板

为每个可供 Agent 调用的 tool 使用以下固定格式。保留英文段落标题，中文填写具体业务语义。不要省略不适用项目，应明确写“无”或说明不适用原因。

```python
from langchain.tools import tool


@tool
def query_city_weather(city_name: str, include_forecast: bool = False) -> dict[str, object]:
    """查询指定城市的当前天气或短期预报。

    Use when:
    - 用户明确询问某个城市的当前天气或短期预报。
    - 已获得足以定位城市的名称与国家或地区信息。

    Do not use when:
    - 用户询问历史气候、灾害预警或医疗、安全决策；应使用相应领域服务或人工流程。
    - 城市名称不明确、请求会产生高成本或需要修改外部资源；应先补充信息或审批。

    Args:
        city_name: 待查询的城市名称。必须是非空文本；会经过首尾空白清理后传给天气服务。
        include_forecast: 是否返回未来预报。默认 `False` 只返回当前天气；仅允许布尔值。

    Returns:
        返回包含 `status` 的字典及其关键字段含义。
        成功时: {"status": "success", "data": {"city": "...", "weather": "..."}}
        失败时: {"status": "error", "error": {"code": "...", "message": "..."}}

    Side effects:
    - 无。本工具只读取天气服务，不创建、修改、删除或发送外部资源。

    Preconditions:
    - `city_name` 必须可用于定位目标城市。
    - 调用方必须具备使用天气服务的网络与服务权限。

    Errors:
    - invalid_input: `city_name` 为空，或 `include_forecast` 不是布尔值。
    - not_found: 天气服务中找不到目标城市。
    - permission_denied: 当前运行身份无权访问天气服务。
    - external_service_error: 天气服务超时、限流或发生临时错误；只有只读请求才可安全重试。

    Examples:
        query_city_weather(city_name="Shanghai", include_forecast=True)

    Notes:
    - 工具是只读且幂等的；同一参数的多次调用不会修改外部状态。
    - 返回时间应标明时区；生产实现还应记录数据来源、缓存时间和速率限制策略。
    """
    if not city_name.strip():
        return {
            "status": "error",
            "error": {"code": "invalid_input", "message": "City name is required."},
        }

    return {
        "status": "success",
        "data": {"city": city_name.strip(), "weather": "Sunny", "include_forecast": include_forecast},
    }
```

## 使用规则

- 第一行必须以动词开头，描述用户可见结果，不描述内部实现。
- 用 `Use when` 和 `Do not use when` 划清可调用与禁止调用边界。
- 用稳定的 `status`、`data`、`error.code` 和 `error.message` 结构描述结果；不要用模糊字符串代替可解析失败状态。
- 只有声明为只读且幂等的操作才可以在 `external_service_error` 时安全重试。
- 将权限、资源存在性、金额单位、时区、分页、限流和不可逆副作用写入对应段落，不依赖模型自行推断。
