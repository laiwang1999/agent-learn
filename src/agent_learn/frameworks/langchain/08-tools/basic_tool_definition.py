"""演示 `@tool`、Pydantic schema 与模型可见契约的离线验证。"""

from typing import Literal

from langchain.tools import tool
from pydantic import BaseModel, Field


lesson_catalog = {
    "course-001": {"course_title": "LangChain 工具实践", "lesson_count": 12},
    "course-002": {"course_title": "LangGraph 状态实践", "lesson_count": 10},
}


@tool
def search_lesson_catalog(query: str, limit: int = 5) -> dict[str, object]:
    """按课程标题关键词搜索本地课程目录。

    Use when:
    - 用户询问课程名称、主题或编号相关的目录信息。
    - 需要返回可验证的结构化搜索结果，而不是由模型编造课程列表。

    Do not use when:
    - 用户请求报名、修改课程或关键词过于模糊；应先补充信息或转入业务流程。
    - 需要跨租户或实时外部目录；应使用受权限控制的专用集成。

    Args:
        query: 搜索关键词。必须是非空文本；会清理首尾空白后在本地目录中匹配标题。
        limit: 返回结果数量上限。默认 5；必须为正整数。

    Returns:
        返回包含 `status` 的字典及其关键字段含义。
        成功时: {"status": "success", "data": {"query": "...", "results": [...]}}
        失败时: {"status": "error", "error": {"code": "...", "message": "..."}}

    Side effects:
    - 无。本工具只读取进程内演示数据，不创建、修改、删除或发送外部资源。

    Preconditions:
    - `query` 必须可用于匹配课程标题。
    - `limit` 必须大于 0。

    Errors:
    - invalid_input: `query` 为空，或 `limit` 不是正整数。
    - not_found: 本地目录中没有匹配课程。
    - permission_denied: 不适用；本示例不包含权限系统。
    - external_service_error: 不适用；本示例不调用外部服务。

    Examples:
        search_lesson_catalog(query="LangChain", limit=3)

    Notes:
    - 本工具只读且幂等；相同参数的重复调用不会修改目录。
    - 生产实现应记录数据来源、分页策略和速率限制，并避免把内部 ID 无边界暴露给模型。
    """
    normalized_query = query.strip().lower()
    if not normalized_query:
        return {
            "status": "error",
            "error": {"code": "invalid_input", "message": "Search query is required."},
        }
    if limit <= 0:
        return {
            "status": "error",
            "error": {"code": "invalid_input", "message": "Limit must be a positive integer."},
        }

    # 确定性搜索交给 Python 执行，避免模型根据课程名称猜测数量或编造条目。
    results = [
        {"product_id": product_id, **product}
        for product_id, product in lesson_catalog.items()
        if normalized_query in product["course_title"].lower()
    ][:limit]

    if not results:
        return {
            "status": "error",
            "error": {"code": "not_found", "message": "No matching courses were found."},
        }

    return {
        "status": "success",
        "data": {"query": normalized_query, "results": results},
    }


class WeatherInput(BaseModel):
    """天气查询输入 schema，用于约束枚举值与字段描述。"""

    city_name: str = Field(description="城市名称或坐标文本")
    units: Literal["celsius", "fahrenheit"] = Field(
        default="celsius",
        description="温度单位偏好",
    )
    include_forecast: bool = Field(
        default=False,
        description="是否包含未来五天预报",
    )


@tool("get_city_weather", args_schema=WeatherInput)
def get_city_weather(
    city_name: str,
    units: str = "celsius",
    include_forecast: bool = False,
) -> dict[str, object]:
    """查询指定城市的当前天气与可选预报。

    Use when:
    - 用户明确询问某个城市的当前天气或短期预报。
    - 城市名称足以定位目标地点。

    Do not use when:
    - 用户询问历史气候、灾害预警或需要医疗、出行安全决策；应使用专业数据源。
    - 城市名称不明确；应先补充国家或地区信息。

    Args:
        city_name: 待查询城市名称。必须是非空文本。
        units: 温度单位，仅允许 `celsius` 或 `fahrenheit`。
        include_forecast: 是否返回预报摘要。

    Returns:
        返回包含 `status` 的字典及其关键字段含义。
        成功时: {"status": "success", "data": {"city_name": "...", "temperature_c": 0, ...}}
        失败时: {"status": "error", "error": {"code": "...", "message": "..."}}

    Side effects:
    - 无。本示例返回固定演示数据，不访问真实天气服务。

    Preconditions:
    - `city_name` 必须可用于定位城市。

    Errors:
    - invalid_input: `city_name` 为空或只有空白字符。
    - not_found: 不适用；演示数据对所有非空城市返回固定结果。
    - permission_denied: 不适用；本示例不包含权限系统。
    - external_service_error: 不适用；本示例不调用外部服务。

    Examples:
        get_city_weather(city_name="Shanghai", units="celsius", include_forecast=True)

    Notes:
    - 复杂参数通过 `WeatherInput` 暴露字段级描述，能减少模型误填枚举值。
    - 生产实现必须校验模型能力与多模态返回格式是否匹配。
    """
    normalized_city_name = city_name.strip()
    if not normalized_city_name:
        return {
            "status": "error",
            "error": {"code": "invalid_input", "message": "City name is required."},
        }

    temperature_c = 22
    payload: dict[str, object] = {
        "city_name": normalized_city_name,
        "temperature_c": temperature_c,
        "conditions": "sunny",
        "units": units,
    }
    if include_forecast:
        payload["forecast_summary"] = "Five sunny days with stable temperatures."

    return {"status": "success", "data": payload}


def describe_tool_for_model(tool_obj) -> dict[str, object]:
    """提取模型可见的工具名、描述与参数 schema，便于离线审查契约。"""
    schema = tool_obj.get_input_schema().model_json_schema()
    return {
        "name": tool_obj.name,
        "description": tool_obj.description,
        "parameters": schema.get("properties", {}),
        "required": schema.get("required", []),
    }


def runtime_is_hidden_from_tool_args(tool_obj) -> bool:
    """确认 `runtime` 与 `config` 没有出现在模型可见参数中。"""
    exposed_names = set(tool_obj.args.keys())
    reserved_names = {"runtime", "config"}
    return reserved_names.isdisjoint(exposed_names)


def runtime_is_hidden_from_schema(schema: dict[str, object]) -> bool:
    """确认 JSON schema 的 properties 中没有保留参数名。"""
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        return False
    reserved_names = {"runtime", "config"}
    exposed_names = set(properties.keys())
    return reserved_names.isdisjoint(exposed_names)


def main() -> None:
    catalog_description = describe_tool_for_model(search_lesson_catalog)
    weather_description = describe_tool_for_model(get_city_weather)

    print("课程搜索工具 schema：", catalog_description)
    print("天气工具 schema：", weather_description)
    print(
        "课程搜索结果：",
        search_lesson_catalog.invoke({"query": "LangChain", "limit": 2}),
    )
    print(
        "天气查询结果：",
        get_city_weather.invoke(
            {"city_name": "Shanghai", "units": "celsius", "include_forecast": True}
        ),
    )

    weather_schema = get_city_weather.get_input_schema().model_json_schema()
    assert runtime_is_hidden_from_schema(weather_schema)


if __name__ == "__main__":
    main()
