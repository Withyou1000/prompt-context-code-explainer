from __future__ import annotations

import hashlib
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
    outputs: list[str] = []

    for _ in range(5):
        result = explain_code_with_llm(code)
        outputs.append(json.dumps(result, ensure_ascii=False, sort_keys=True))

    hashes = [hashlib.sha256(item.encode("utf-8")).hexdigest() for item in outputs]
    stable = len(set(hashes)) == 1

    print(json.dumps({
        "backend": "llm",
        "runs": 5,
        "stable": stable,
        "hashes": hashes,
    }, ensure_ascii=False, indent=2))

    return 0 if stable else 1


if __name__ == "__main__":
    raise SystemExit(main())
