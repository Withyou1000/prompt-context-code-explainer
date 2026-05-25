from __future__ import annotations

import ast
import json
from pathlib import Path

from .contract import BugInfo, CodeExplanation, InputInfo, OutputInfo, TestSuggestion


def explain_code(code: str) -> CodeExplanation:
    """用 Python AST 生成稳定的代码解释结果。"""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return CodeExplanation(
            function_name="",
            summary="代码存在语法错误，无法完成函数级解释。",
            limitations=[f"语法错误：第 {exc.lineno} 行，{exc.msg}"],
            confidence="low",
        )

    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    if not functions:
        return CodeExplanation(
            function_name="",
            summary="未识别到顶层 Python 函数定义。",
            limitations=["输入代码中没有顶层 def 函数。"],
            confidence="low",
        )

    function = functions[0]
    facts = collect_facts(function)

    inputs = build_inputs(function)
    outputs = build_outputs(facts)
    bugs = detect_potential_bugs(facts)
    tests = build_test_suggestions(function, facts, bugs)

    return CodeExplanation(
        function_name=function.name,
        summary=build_summary(function, facts),
        inputs=inputs,
        outputs=outputs,
        potential_bugs=bugs,
        test_suggestions=tests,
        limitations=[] if len(functions) == 1 else ["只解释了第一个顶层函数。"],
        confidence="high" if outputs else "medium",
    )


def explain_file(path: str | Path) -> CodeExplanation:
    code = Path(path).read_text(encoding="utf-8")
    return explain_code(code)


def collect_facts(function: ast.FunctionDef) -> dict:
    returns: list[str] = []
    divisions: list[str] = []
    len_calls: list[str] = []
    subscript_accesses: list[str] = []
    raised_exceptions: list[str] = []

    for node in ast.walk(function):
        if isinstance(node, ast.Return):
            returns.append(to_source(node.value) if node.value else "None")
        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
            divisions.append(to_source(node))
        elif isinstance(node, ast.Call) and call_name(node) == "len":
            len_calls.append(to_source(node))
        elif isinstance(node, ast.Subscript):
            subscript_accesses.append(to_source(node))
        elif isinstance(node, ast.Raise):
            raised_exceptions.append(to_source(node.exc) if node.exc else "raise")

    return {
        "returns": returns,
        "divisions": divisions,
        "len_calls": len_calls,
        "subscript_accesses": subscript_accesses,
        "raised_exceptions": raised_exceptions,
        "has_loop": any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(function)),
        "has_branch": any(isinstance(node, ast.If) for node in ast.walk(function)),
    }


def facts_as_json(code: str) -> str:
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        facts = {"syntax_error": {"line": exc.lineno, "message": exc.msg}}
        return json.dumps(facts, ensure_ascii=False, indent=2, sort_keys=True)

    function = next((node for node in tree.body if isinstance(node, ast.FunctionDef)), None)
    facts = collect_facts(function) if function else {"error": "未找到顶层函数"}
    return json.dumps(facts, ensure_ascii=False, indent=2, sort_keys=True)


def build_inputs(function: ast.FunctionDef) -> list[InputInfo]:
    args = function.args.args
    defaults = [None] * (len(args) - len(function.args.defaults))
    defaults.extend(to_source(default) for default in function.args.defaults)

    inputs: list[InputInfo] = []
    for arg, default in zip(args, defaults):
        role = infer_input_role(arg.arg)
        inputs.append(InputInfo(name=arg.arg, role=role, default=default))
    return inputs


def build_outputs(facts: dict) -> list[OutputInfo]:
    returns = facts["returns"]
    if not returns:
        return [OutputInfo(kind="implicit", description="函数没有显式 return，默认返回 None。")]

    return [
        OutputInfo(kind="return", description=f"返回表达式 `{expr}` 的计算结果。")
        for expr in returns
    ]


def detect_potential_bugs(facts: dict) -> list[BugInfo]:
    bugs: list[BugInfo] = []

    for expr in facts["divisions"]:
        bugs.append(
            BugInfo(
                risk="除数为 0 时可能触发 ZeroDivisionError。",
                evidence=f"代码中存在除法或取模表达式：{expr}",
                suggestion="在计算前检查除数是否为 0，或为空集合设置明确返回值。",
            )
        )

    if facts["subscript_accesses"]:
        bugs.append(
            BugInfo(
                risk="索引访问在集合为空或索引越界时可能触发异常。",
                evidence=f"代码中存在下标访问：{', '.join(facts['subscript_accesses'])}",
                suggestion="访问前检查集合长度，或捕获并处理 IndexError/KeyError。",
            )
        )

    return bugs


def build_test_suggestions(
    function: ast.FunctionDef,
    facts: dict,
    bugs: list[BugInfo],
) -> list[TestSuggestion]:
    args = [arg.arg for arg in function.args.args]
    tests: list[TestSuggestion] = []

    if args:
        normal_values = ", ".join(f"{name}=示例值" for name in args)
        tests.append(TestSuggestion(case=normal_values, reason="验证普通输入下的主要功能。"))
    else:
        tests.append(TestSuggestion(case="无参数调用", reason="验证函数可以正常执行。"))

    if facts["len_calls"] or any("空" in bug.risk or "除数" in bug.risk for bug in bugs):
        tests.append(TestSuggestion(case="传入空列表或空集合", reason="验证空输入边界和除零风险。"))

    if facts["subscript_accesses"]:
        tests.append(TestSuggestion(case="传入长度不足的集合", reason="验证索引越界风险。"))

    if not tests:
        tests.append(TestSuggestion(case="构造最小有效输入", reason="验证基础路径。"))

    return tests


def build_summary(function: ast.FunctionDef, facts: dict) -> str:
    if facts["returns"]:
        return f"函数 `{function.name}` 根据输入参数计算并返回 `{facts['returns'][0]}`。"
    return f"函数 `{function.name}` 执行一段过程逻辑，但没有显式返回值。"


def infer_input_role(name: str) -> str:
    lower = name.lower()
    if lower in {"nums", "numbers", "items", "arr", "lst", "values"}:
        return "参与计算或遍历的数据集合"
    if lower in {"x", "y", "n", "a", "b"}:
        return "参与计算的输入值"
    if "path" in lower or "file" in lower:
        return "文件或路径参数"
    return "函数逻辑使用的输入参数"


def call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def to_source(node: ast.AST | None) -> str:
    if node is None:
        return "None"
    try:
        return ast.unparse(node)
    except Exception:
        return node.__class__.__name__
