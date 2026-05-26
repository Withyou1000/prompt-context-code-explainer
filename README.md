# 代码解释助手

这是一个用于练习 Prompt 和上下文工程的 Python 小项目。

项目接收一段 Python 函数代码，调用 OpenAI 兼容大模型接口，输出结构化的代码解释结果，包括：

- 功能说明
- 输入参数
- 输出结果
- 潜在 bug
- 测试建议
- 限制说明
- 置信度

## 项目结构

```text
.
├── examples/
│   └── sample_function.py
├── prompts/
│   ├── system.zh.md
│   └── code_explainer.zh.md
├── src/
│   └── code_explainer/
│       ├── __init__.py
│       ├── cli.py
│       ├── llm_client.py
│       └── prompting.py
├── tests/
│   └── stability_check.py
├── .env.example
├── main.py
├── pyproject.toml
└── 学习材料.md
```

## 环境配置

项目使用 `uv` 管理 Python 依赖。

首次运行前，在项目根目录新建 `.env` 文件，可以参考 `.env.example`：

```env
OPENAI_API_KEY=你的 API Key
OPENAI_BASE_URL=https://ai.12zx.net/v1
OPENAI_API_MODE=chat
OPENAI_MODEL=gpt-5.4
OPENAI_USER_AGENT=OpenAI/Python 1.0.0
OPENAI_INPUT_PRICE_PER_1M=0
OPENAI_OUTPUT_PRICE_PER_1M=0
```

`.env` 已加入 `.gitignore`，不要把真实 API Key 提交到仓库。

## 使用方式

解释示例函数：

```powershell
uv run python -m src.code_explainer.cli examples/sample_function.py
```

查看最终组装出的 Prompt：

```powershell
uv run python -m src.code_explainer.cli examples/sample_function.py --show-prompt
```

连续调用 5 次，检查输出结构是否稳定：

```powershell
uv run python tests/stability_check.py examples/sample_function.py
```

也可以通过 `main.py` 运行：

```powershell
uv run python main.py examples/sample_function.py
```

## 示例输入

```python
def average(nums):
    total = sum(nums)
    return total / len(nums)
```

## 示例输出

实际输出由大模型生成，结构应保持为 JSON：

```json
{
  "function_name": "average",
  "summary": "计算 nums 中所有元素的平均值。",
  "inputs": [],
  "outputs": [],
  "potential_bugs": [],
  "test_suggestions": [],
  "limitations": [],
  "confidence": "high"
}
```

## 说明

如果接口返回 `HTTP 403` 或 Cloudflare 拦截信息，通常不是项目代码问题，而是 `OPENAI_BASE_URL` 对脚本请求做了限制。可以更换可用的 OpenAI 兼容接口，或联系服务提供方放行 API 调用。
