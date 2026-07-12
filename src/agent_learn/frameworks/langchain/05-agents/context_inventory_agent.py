"""演示 `context_schema`、动态提示和 `thread_id` 的职责边界。"""

from dataclasses import dataclass

from langchain.agents import create_agent
from langchain.tools import ToolRuntime, tool
from langgraph.checkpoint.memory import InMemorySaver

from minimal_inventory_agent import create_chat_model
from langchain.agents.middleware import ModelRequest, dynamic_prompt

@dataclass(frozen=True, slots=True)
class RuntimeContext:
    """描述本次请求的租户与权限，避免把运行时权限混入对话 messages。"""

    tenant_name: str
    can_view_inventory: bool


# 租户库存用于演示运行时隔离；生产环境应通过认证后的租户标识查询受控数据源。
tenant_inventory_data = {
    "learning-team": {"course-001": 8},
    "demo-team": {"course-001": 2},
}


@tool
def lookup_tenant_inventory(product_id: str, runtime: ToolRuntime[RuntimeContext]) -> dict[str, object]:
    """查询当前租户内指定商品的库存。

    Use when:
    - 用户明确询问当前租户内具有已知商品编号的库存。
    - 服务端已提供可信的 `RuntimeContext`，且其中授予库存查看权限。

    Do not use when:
    - 用户请求跨租户数据、修改库存或商品编号不明确；应拒绝、补充提问或转入审批流程。
    - 权限上下文缺失，或操作可能导致高成本、不可逆影响；应先完成认证和授权。

    Args:
        product_id: 待查询的商品编号，例如 `course-001`。必须是非空文本；清理首尾空白后用于查找。
        runtime: 由 LangChain 注入的运行时对象，不会暴露给模型的 tool schema。其 context 必须为可信的 `RuntimeContext`。

    Returns:
        返回包含 `status` 的字典及其关键字段含义。
        成功时: {"status": "success", "data": {"tenant_name": "...", "product_id": "...", "available_quantity": 0}}
        失败时: {"status": "error", "error": {"code": "...", "message": "..."}}

    Side effects:
    - 无。本工具只读取进程内演示数据，不创建、修改、删除或发送外部资源。

    Preconditions:
    - `runtime.context` 必须存在，并包含经过认证的租户名称与 `can_view_inventory=True`。
    - `product_id` 必须是可查询的非空文本。

    Errors:
    - invalid_input: `product_id` 为空或只有空白字符，或运行时 context 缺失。
    - not_found: 当前租户不存在目标商品。
    - permission_denied: 当前租户没有库存查看权限。
    - external_service_error: 不适用；本示例不调用外部服务，因此不存在可安全重试的服务错误。

    Examples:
        lookup_tenant_inventory(product_id="course-001", runtime=runtime)

    Notes:
    - 本工具只读且幂等；同一租户和商品的重复调用不会修改库存。
    - 生产实现必须在调用前完成认证与授权，并审计访问；不得信任用户在 messages 中声称的权限。
    """
    # runtime.context 是服务端传入的可信数据；它与用户可编辑的 messages 保持隔离。
    context = runtime.context
    if context is None:
        return {
            "status": "error",
            "error": {"code": "invalid_input", "message": "Runtime context is required."},
        }
    if not context.can_view_inventory:
        return {
            "status": "error",
            "error": {"code": "permission_denied", "message": "Inventory access is not allowed."},
        }

    normalized_product_id = product_id.strip()
    if not normalized_product_id:
        return {
            "status": "error",
            "error": {"code": "invalid_input", "message": "Product ID is required."},
        }

    # 先按租户取数，再按商品查询，避免示例误导读者以为不同租户可共享库存视图。
    tenant_inventory = tenant_inventory_data.get(context.tenant_name, {})
    available_quantity = tenant_inventory.get(normalized_product_id)
    if available_quantity is None:
        return {
            "status": "error",
            "error": {"code": "not_found", "message": "Product was not found for this tenant."},
        }

    return {
        "status": "success",
        "data": {
            "tenant_name": context.tenant_name,
            "product_id": normalized_product_id,
            "available_quantity": available_quantity,
        },
    }


@dynamic_prompt
def build_permission_prompt(request: ModelRequest[RuntimeContext]) -> str:
    context = request.runtime.context
    if context is None or not context.can_view_inventory:
        return "你是一名库存助手。当前请求未获得库存访问权限，不得调用库存查询工具。最终答复必须使用中文。"
    return (
        f"你是租户 {context.tenant_name} 的库存助手。回答库存问题时必须调用 "
        "lookup_tenant_inventory，禁止访问其他租户的数据。最终答复必须使用中文。"
    )


def create_permission_inventory_agent():
    """创建带短期 memory、runtime context 和动态提示的库存 Agent。"""
    # checkpointer 与 thread_id 共同保存同一会话历史；本地 InMemorySaver 仅用于学习演示。
    return create_agent(
        model=create_chat_model(),
        tools=[lookup_tenant_inventory],
        context_schema=RuntimeContext,
        middleware=[build_permission_prompt],
        checkpointer=InMemorySaver(),
        name="permission_inventory_agent",
    )


def main() -> None:
    agent = create_permission_inventory_agent()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "course-001 目前还有多少库存？"}]},
        config={"configurable": {"thread_id": "learning-team-inventory-session"}},
        context=RuntimeContext(tenant_name="learning-team", can_view_inventory=True),
    )
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
