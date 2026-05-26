from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from dotenv import load_dotenv

from .prompting import build_prompt


class LLMError(RuntimeError):
    """大模型调用失败时抛出的异常。"""


def explain_code_with_llm(code: str) -> dict:
    """调用 OpenAI 兼容接口，让大模型按 Prompt 契约解释代码。"""
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMError("缺少环境变量 OPENAI_API_KEY，无法调用大模型。")

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-5.4")
    api_mode = os.getenv("OPENAI_API_MODE", "chat")
    if api_mode != "chat":
        raise LLMError(f"当前只支持 OPENAI_API_MODE=chat，实际值是 {api_mode!r}。")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "你是严谨的代码解释助手。必须只输出合法 JSON，不要输出 Markdown。",
            },
            {
                "role": "user",
                "content": build_prompt(code),
            },
        ],
        "temperature": 0,
    }

    response_text = post_json(f"{base_url}/chat/completions", payload, api_key)
    data = json.loads(response_text)

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError("大模型响应格式不符合 chat/completions 约定。") from exc

    return parse_json_content(content)


def post_json(url: str, payload: dict, api_key: str) -> str:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": os.getenv("OPENAI_USER_AGENT", "OpenAI/Python 1.0.0"),
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise LLMError(f"大模型接口返回 HTTP {exc.code}：{detail}") from exc
    except urllib.error.URLError as exc:
        raise LLMError(f"无法连接大模型接口：{exc.reason}") from exc


def parse_json_content(content: str) -> dict:
    """兼容模型偶尔包一层 ```json 代码块的情况。"""
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError(f"大模型没有返回合法 JSON：{content}") from exc
