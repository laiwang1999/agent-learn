"""提供跨章节复用的本地环境配置读取能力。"""

from collections.abc import Mapping
from os import environ

from dotenv import load_dotenv


def load_project_environment() -> None:
    """从项目根目录的 `.env` 载入尚未存在的环境变量。"""
    # 已由部署平台或终端设置的变量优先，避免本地文件意外覆盖生产配置。
    load_dotenv(override=False)


def get_required_environment_variable(
    variable_name: str, environment: Mapping[str, str] | None = None
) -> str:
    """读取非空配置，并在缺失时给出不包含密钥的明确错误。"""
    # 先验证变量名，避免错误信息本身无法帮助调用方定位配置问题。
    if not variable_name.strip():
        raise ValueError("Environment variable name is required.")

    source = environ if environment is None else environment
    value = source.get(variable_name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {variable_name}")
    return value
