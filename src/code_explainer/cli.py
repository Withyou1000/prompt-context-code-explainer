from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .analyzer import explain_code
from .prompting import build_prompt


def main(argv: list[str] | None = None) -> int:
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
        print(build_prompt(code))
        return 0

    explanation = explain_code(code)
    print(json.dumps(explanation.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
