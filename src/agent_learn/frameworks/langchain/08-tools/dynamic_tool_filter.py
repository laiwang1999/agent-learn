"""演示如何按认证状态与角色动态过滤模型可见工具集合。"""

from dataclasses import dataclass

from langchain.tools import BaseTool, tool


@dataclass(frozen=True, slots=True)
class ToolAccessContext:
    """描述本次请求的工具访问上下文，应由服务端认证后注入。"""

    is_authenticated: bool
    user_role: str


@tool
def public_search_catalog(query: str) -> dict[str, object]:
    """搜索公开课程目录中的关键词。

    Use when:
    - 访客或未登录用户需要查询公开课程信息。

    Do not use when:
    - 需要租户私有目录或写操作；应使用认证后的专用工具。

    Args:
        query: 搜索关键词，必须为非空文本。

    Returns:
        成功时: {"status": "success", "data": {"query": "...", "visibility": "public"}}
        失败时: {"status": "error", "error": {"code": "...", "message": "..."}}

    Side effects:
    - 无。

    Preconditions:
    - `query` 必须为非空文本。

    Errors:
    - invalid_input: `query` 为空。
    - not_found: 不适用；演示实现始终返回成功。
    - permission_denied: 不适用；公开工具不要求登录。
    - external_service_error: 不适用。

    Examples:
        public_search_catalog(query="agent")

    Notes:
    - 工具名以 `public_` 前缀标识访客可见能力，便于动态过滤。
    """
    normalized_query = query.strip()
    if not normalized_query:
        return {
            "status": "error",
            "error": {"code": "invalid_input", "message": "Search query is required."},
        }
    return {
        "status": "success",
        "data": {"query": normalized_query, "visibility": "public"},
    }


@tool
def read_tenant_inventory(product_id: str) -> dict[str, object]:
    """读取当前租户内商品库存。

    Use when:
    - 已认证用户需要查询自己租户内的库存事实。

    Do not use when:
    - 用户未登录或只有访客权限；应拒绝或只暴露公开工具。

    Args:
        product_id: 商品编号，必须为非空文本。

    Returns:
        成功时: {"status": "success", "data": {"product_id": "...", "available_quantity": 0}}
        失败时: {"status": "error", "error": {"code": "...", "message": "..."}}

    Side effects:
    - 无。

    Preconditions:
    - 调用方必须已完成认证，并在 middleware 中授予读库存权限。

    Errors:
    - invalid_input: `product_id` 为空。
    - not_found: 不适用；演示实现始终返回成功。
    - permission_denied: 当前身份无权读取库存。
    - external_service_error: 不适用。

    Examples:
        read_tenant_inventory(product_id="course-001")

    Notes:
    - 工具名以 `read_` 前缀标识只读业务操作，便于按角色过滤。
    """
    normalized_product_id = product_id.strip()
    if not normalized_product_id:
        return {
            "status": "error",
            "error": {"code": "invalid_input", "message": "Product ID is required."},
        }
    return {
        "status": "success",
        "data": {"product_id": normalized_product_id, "available_quantity": 8},
    }


@tool
def write_inventory_adjustment(product_id: str, delta: int) -> dict[str, object]:
    """提交库存调整请求。

    Use when:
    - 已授权编辑者需要修改库存，并经过业务流程确认。

    Do not use when:
    - 当前用户只有访客或只读权限；必须拒绝暴露该工具。
    - 调整数量不明确或可能产生不可逆影响；应先人工审批。

    Args:
        product_id: 商品编号，必须为非空文本。
        delta: 库存增减数量，必须为整数。

    Returns:
        成功时: {"status": "success", "data": {"product_id": "...", "delta": 0}}
        失败时: {"status": "error", "error": {"code": "...", "message": "..."}}

    Side effects:
    - 演示实现不真正修改数据；生产实现会改变库存记录并产生审计日志。

    Preconditions:
    - 调用方必须具备写库存权限，并经过幂等与审批检查。

    Errors:
    - invalid_input: `product_id` 为空。
    - not_found: 不适用；演示实现始终返回成功。
    - permission_denied: 当前身份无权修改库存。
    - external_service_error: 不适用。

    Examples:
        write_inventory_adjustment(product_id="course-001", delta=-1)

    Notes:
    - 写操作工具应配合 guardrails 或 human-in-the-loop，而不是长期对所有角色开放。
    """
    normalized_product_id = product_id.strip()
    if not normalized_product_id:
        return {
            "status": "error",
            "error": {"code": "invalid_input", "message": "Product ID is required."},
        }
    return {
        "status": "success",
        "data": {"product_id": normalized_product_id, "delta": delta},
    }


def filter_tools_by_authentication(tools: list[BaseTool], is_authenticated: bool) -> list[BaseTool]:
    """未登录时只保留 `public_` 前缀工具，减少模型误选私有能力。"""
    if is_authenticated:
        return list(tools)
    return [tool_obj for tool_obj in tools if tool_obj.name.startswith("public_")]


def filter_tools_by_role(tools: list[BaseTool], user_role: str) -> list[BaseTool]:
    """按角色限制读写工具：访客只看公开工具，浏览者只读，编辑者可写。"""
    if user_role == "viewer":
        return [tool_obj for tool_obj in tools if tool_obj.name.startswith(("public_", "read_"))]
    if user_role == "editor":
        return list(tools)
    return [tool_obj for tool_obj in tools if tool_obj.name.startswith("public_")]


def select_tools_for_request(tools: list[BaseTool], context: ToolAccessContext) -> list[BaseTool]:
    """组合认证与角色两层过滤，得到本次模型调用应暴露的工具集合。"""
    authenticated_tools = filter_tools_by_authentication(tools, context.is_authenticated)
    return filter_tools_by_role(authenticated_tools, context.user_role)


def list_tool_names(tools: list[BaseTool]) -> list[str]:
    """提取工具名列表，便于打印和断言。"""
    return [tool_obj.name for tool_obj in tools]


def build_demo_toolset() -> list[BaseTool]:
    """构造包含公开、只读、写操作三类能力的演示工具集合。"""
    return [public_search_catalog, read_tenant_inventory, write_inventory_adjustment]


def main() -> None:
    tools = build_demo_toolset()

    guest_tools = select_tools_for_request(
        tools,
        ToolAccessContext(is_authenticated=False, user_role="guest"),
    )
    viewer_tools = select_tools_for_request(
        tools,
        ToolAccessContext(is_authenticated=True, user_role="viewer"),
    )
    editor_tools = select_tools_for_request(
        tools,
        ToolAccessContext(is_authenticated=True, user_role="editor"),
    )

    print("访客可见工具：", list_tool_names(guest_tools))
    print("浏览者可见工具：", list_tool_names(viewer_tools))
    print("编辑者可见工具：", list_tool_names(editor_tools))


if __name__ == "__main__":
    main()
