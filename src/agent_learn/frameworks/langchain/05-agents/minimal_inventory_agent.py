"""演示 `create_agent` 如何把模型和工具组合为最小 Agent loop。"""

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from agent_learn.shared.environment import (
    get_required_environment_variable,
    load_project_environment,
)


# 使用固定数据让工具结果可预测；真实项目应替换为受权限控制的库存服务。
inventory_data = {
    "book-001": {"name": "Agent Engineering Introduction", "available_quantity": 12},
    "book-002": {"name": "LangGraph State Management", "available_quantity": 0},
}


@tool
def lookup_product_inventory(product_id: str) -> dict[str, object]:
    """查询指定商品的可用库存。

    Use when:
    - 用户询问具有明确商品编号的当前库存。
    - 需要返回可验证的库存事实，而不是由模型猜测数量。

    Do not use when:
    - 用户请求下单、扣减库存、预测销量或商品编号不明确；应转入业务流程或补充提问。
    - 请求涉及高成本、不可逆或跨租户操作；应使用受审批的专用工具。

    Args:
        product_id: 待查询的唯一商品编号，例如 `book-001`。必须是非空文本；清理首尾空白后用于查找。

    Returns:
        返回包含 `status` 的字典及其关键字段含义。
        成功时: {"status": "success", "data": {"product_id": "...", "name": "...", "available_quantity": 0}}
        失败时: {"status": "error", "error": {"code": "...", "message": "..."}}

    Side effects:
    - 无。本工具只读取进程内演示数据，不创建、修改、删除或发送外部资源。

    Preconditions:
    - `product_id` 必须是可查询的非空文本。

    Errors:
    - invalid_input: `product_id` 为空或只有空白字符。
    - not_found: 演示库存中不存在目标商品。
    - permission_denied: 不适用；本示例不包含权限系统。
    - external_service_error: 不适用；本示例不调用外部服务，因此不存在可重试的服务错误。

    Examples:
        lookup_product_inventory(product_id="book-001")

    Notes:
    - 本工具只读且幂等；相同输入的重复调用不会修改库存。
    - 生产实现应返回库存观测时间、数据来源和缓存状态，并处理服务限流与超时。
    """
    # 先验证输入，避免把空编号误判为库存不足并返回错误事实。
    normalized_product_id = product_id.strip()
    if not normalized_product_id:
        return {
            "status": "error",
            "error": {"code": "invalid_input", "message": "Product ID is required."},
        }

    # 库存查询属于确定性读取，交给 Python 代码执行比让模型猜测数量更可靠。
    product = inventory_data.get(normalized_product_id)
    if product is None:
        return {
            "status": "error",
            "error": {"code": "not_found", "message": "Product was not found."},
        }

    return {
        "status": "success",
        "data": {"product_id": normalized_product_id, **product},
    }


def create_chat_model() -> ChatOpenAI:
    """创建通过 DeepSeek OpenAI-compatible API 访问的对话模型实例。"""
    # 在读取配置前载入本地 .env，同时保留部署环境变量的优先级。
    load_project_environment()
    return ChatOpenAI(
        model=get_required_environment_variable("AGENT_MODEL"),
        api_key=get_required_environment_variable("DEEPSEEK_API_KEY"),
        base_url=get_required_environment_variable("DEEPSEEK_BASE_URL"),
        temperature=float(get_required_environment_variable("AGENT_TEMPERATURE")),
        timeout=int(get_required_environment_variable("AGENT_TIMEOUT_SECONDS")),
        max_tokens=int(get_required_environment_variable("AGENT_MAX_TOKENS")),
    )


def create_inventory_agent():
    """创建由模型、库存 tool 与行为约束组成的最小 LangChain Agent。"""
    # create_agent 负责模型与工具之间的循环；模型决定何时调用工具，工具返回可验证事实。
    return create_agent(
        model=create_chat_model(),
        tools=[lookup_product_inventory],
        system_prompt=(
            "你是一名库存助手。回答库存问题时必须调用 lookup_product_inventory，"
            "禁止猜测数量。商品编号缺失时必须要求用户提供编号。最终答复必须使用中文。"
        ),
        name="inventory_agent",
    )


def main() -> None:
    agent = create_inventory_agent()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "book-001 目前还有多少库存？"}]}
    )
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
