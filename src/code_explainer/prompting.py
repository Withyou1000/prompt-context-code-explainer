from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROMPT_TEMPLATE = ROOT / "prompts" / "code_explainer.zh.md"


def build_prompt(code: str) -> str:
    """把用户代码填入 Prompt 模板。"""
    template = PROMPT_TEMPLATE.read_text(encoding="utf-8")
    return template.replace("{{code}}", code.strip())
