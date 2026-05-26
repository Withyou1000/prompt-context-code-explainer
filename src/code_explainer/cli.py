from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .prompting import build_prompt


def main(argv: list[str] | None = None) -> int:
    # argparse 负责把命令行里的文件路径和开关参数解析成 args 对象。
    parser = argparse.ArgumentParser(description="稳定输出的代码解释助手")
    parser.add_argument("file", help="要解释的 Python 函数文件")
    parser.add_argument("--show-prompt", action="store_true", help="只显示组装后的 Prompt")
    args = parser.parse_args(argv)

    path = Path(args.file)
    if not path.exists():
        print(f"文件不存在：{path}", file=sys.stderr)
        return 2

    code = path.read_text(encoding="utf-8")

    if args.show_prompt:
        # 调试 Prompt 时不需要加载大模型依赖，也不会真的发起网络请求。
        print(build_prompt(code))
        return 0

    try:
        # 延迟导入可以让 --show-prompt 在未安装 python-dotenv 时也能正常使用。
        from .llm_client import LLMError, explain_code_with_llm

        explanation = explain_code_with_llm(code)
    except LLMError as exc:
        # 大模型调用失败时仍然输出结构化错误，方便脚本或前端读取。
        print(json.dumps({
            "error_code": "LLM_CALL_FAILED",
            "message": str(exc),
        }, ensure_ascii=False, indent=2, sort_keys=True), file=sys.stderr)
        return 1

    print(json.dumps(explanation, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
