from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.code_explainer.llm_client import explain_code_with_llm  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print("用法：python tests/stability_check.py examples/sample_function.py")
        return 2

    path = Path(sys.argv[1])
    code = path.read_text(encoding="utf-8")

    # 连续调用 5 次，把每次模型输出原样打印出来，方便肉眼对比结构和措辞变化。
    for index in range(1, 3):
        result = explain_code_with_llm(code)
        print(f"\n========== 第 {index} 次输出 ==========\n")
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
