from __future__ import annotations

from pathlib import Path

from .analyzer import facts_as_json


ROOT = Path(__file__).resolve().parents[2]
PROMPT_TEMPLATE = ROOT / "prompts" / "code_explainer.zh.md"


def build_prompt(code: str) -> str:
    """把代码和工具事实填入 Prompt 模板。"""
    template = PROMPT_TEMPLATE.read_text(encoding="utf-8")
    return template.replace("{{code}}", code.strip()).replace("{{facts}}", facts_as_json(code))
