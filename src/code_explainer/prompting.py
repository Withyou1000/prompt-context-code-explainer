from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM_PROMPT = ROOT / "prompts" / "system.zh.md"
PROMPT_TEMPLATE = ROOT / "prompts" / "code_explainer.zh.md"


def read_system_prompt() -> str:
    """读取真正作为 system 消息发送的提示词。"""
    return SYSTEM_PROMPT.read_text(encoding="utf-8").strip()


def build_user_prompt(code: str) -> str:
    """把用户代码填入 Prompt 模板。"""
    template = PROMPT_TEMPLATE.read_text(encoding="utf-8")
    # 模板文件负责保存稳定规则，运行时只替换当前用户输入的代码。
    return template.replace("{{code}}", code.strip())


def build_messages(code: str) -> list[dict[str, str]]:
    """组装实际发送给 chat/completions 的消息列表。"""
    # 只使用 system/user 两类消息，兼容更多 OpenAI 风格的第三方接口。
    return [
        {"role": "system", "content": read_system_prompt()},
        {"role": "user", "content": build_user_prompt(code)},
    ]


def build_prompt(code: str) -> str:
    """展示最终消息，方便调试 Prompt 组装结果。"""
    # 这个函数只用于 --show-prompt，把真实发送的消息分层展示给人看。
    return (
        "## system\n\n"
        f"{read_system_prompt()}\n\n"
        "## user\n\n"
        f"{build_user_prompt(code)}"
    )
