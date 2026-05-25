# 第二阶段：Prompt 和上下文工程

这个项目用一个“代码解释助手”来练习 Prompt 和上下文工程（Context Engineering）。

目标不是只会写一句“请解释代码”，而是学会把模型调用设计成一个稳定系统：输入明确、上下文有序、输出可校验、失败可处理。

## 一、核心技术名词

### 1. 指令分层（Instruction Hierarchy）

大模型收到的内容通常不是一整段 prompt，而是分层消息：

| 层级 | 作用 | 适合放什么 |
| --- | --- | --- |
| system | 最高优先级的身份和总规则 | 你是代码解释助手、必须安全、必须按格式输出 |
| developer | 开发者给模型的执行规范 | 输出字段、分析维度、禁止胡编、错误处理 |
| user | 用户本次具体请求 | 这段函数代码是什么、请解释 |
| tool | 工具返回的事实 | 静态分析结果、文件内容、测试结果 |

错误示例：

```text
请解释下面代码，顺便按 JSON 输出，不要废话，如果有 bug 也说一下。
```

这个 prompt 把身份、任务、格式、边界都混在一起，模型容易不稳定。

更好的分层示例：

```text
system:
你是一个严谨的代码解释助手。你只根据用户提供的代码和工具事实回答。

developer:
你必须输出 JSON，字段固定为 summary、io、bugs、tests、confidence。
如果信息不足，不要猜测，写入 limitations。

user:
请解释下面函数：
def add(a, b):
    return a + b
```

### 2. Few-shot（少样本示例）

Few-shot 是给模型 2-5 个“输入 -> 输出”的示例，让模型模仿稳定结构和判断标准。

不用 few-shot 时，模型可能一次写成段落，一次写成表格，一次写成 JSON。  
加入 few-shot 后，模型更容易保持同一种风格。

示例：

```text
示例输入：
def square(x):
    return x * x

示例输出：
{
  "summary": "计算输入值的平方。",
  "inputs": [{"name": "x", "role": "被平方的值"}],
  "outputs": "返回 x * x 的结果。",
  "potential_bugs": [],
  "test_suggestions": ["x=2 时返回 4", "x=0 时返回 0"]
}
```

### 3. Chain-of-thought 替代方案

不要要求模型暴露完整思考过程，例如“请一步一步说出你的内心推理”。这会带来不稳定、啰嗦和安全问题。

更好的做法是要求模型输出可检查的结果：

| 不推荐 | 推荐 |
| --- | --- |
| 展示你的完整思考过程 | 输出分析步骤清单 |
| 说出你是怎么一步步推理的 | 输出证据：引用了哪些代码行 |
| 把隐藏推理都写出来 | 输出检查项：输入、输出、异常、边界 |

示例：

```json
{
  "analysis_steps": [
    "识别函数签名",
    "提取返回值表达式",
    "检查分支和循环",
    "列出潜在异常"
  ],
  "evidence": [
    "第 2 行 return total / count 可能触发除零错误"
  ]
}
```

### 4. Prompt Template（提示词模板）

Prompt Template 是把 prompt 当成代码管理。

它应该：

- 放在文件里，而不是散落在业务代码字符串中
- 有变量占位符，例如 `{{code}}`
- 能被版本控制
- 能配合测试样例验证输出是否稳定

本项目的模板在：

```text
prompts/code_explainer.zh.md
```

### 5. Context Packing（上下文打包）

Context Packing 是决定“长上下文里放什么、不放什么、怎么排序”。

推荐顺序：

1. 最高优先级规则：角色、边界、输出契约
2. 当前任务：用户要解释的代码
3. 相关事实：静态分析结果、文件名、语言、报错
4. Few-shot 示例：只放最相关的 2-5 个
5. 明确不要放：无关聊天、过长日志、重复代码、未经筛选的资料

坏的上下文会让模型“抽风”：信息太多、顺序混乱、要求互相冲突。

### 6. Output Contract（输出契约）

Output Contract 是明确告诉模型必须输出什么字段、什么类型、边界情况怎么处理。

本项目固定输出：

```json
{
  "function_name": "函数名",
  "summary": "功能说明",
  "inputs": [],
  "outputs": [],
  "potential_bugs": [],
  "test_suggestions": [],
  "limitations": [],
  "confidence": "high | medium | low"
}
```

有了输出契约，后续程序才能解析、测试和比较稳定性。

## 二、项目结构

```text
.
├── examples/
│   └── sample_function.py
├── prompts/
│   └── code_explainer.zh.md
├── src/
│   └── code_explainer/
│       ├── __init__.py
│       ├── analyzer.py
│       ├── cli.py
│       ├── contract.py
│       └── prompting.py
└── tests/
    └── stability_check.py
```

## 三、运行方式

解释示例函数：

```powershell
python -m src.code_explainer.cli examples/sample_function.py
```

连续运行 5 次，检查输出是否稳定：

```powershell
python tests/stability_check.py examples/sample_function.py
```

只查看最终组装出来的 Prompt：

```powershell
python -m src.code_explainer.cli examples/sample_function.py --show-prompt
```

## 四、你应该重点观察什么

1. `prompts/code_explainer.zh.md` 负责把任务讲清楚。
2. `src/code_explainer/contract.py` 负责定义输出结构。
3. `src/code_explainer/analyzer.py` 用 Python AST 做静态分析，提供事实上下文。
4. `tests/stability_check.py` 连续跑 5 次，确认输出结构和内容稳定。

这就是 Prompt 工程变成工程能力的关键：不是赌模型“这次会不会听话”，而是用模板、上下文、契约和测试把它约束住。
