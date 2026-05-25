# AGENTS.md instructions

默认使用中文交流与输出。

## 规则

- 新生成的 README、开发文档、使用说明默认写成简体中文。
- 代码注释默认写成简体中文。
- 如果要生成代码，必要的解释性注释要使用简体中文。
- 除非用户明确要求英文，禁止把新文档默认写成英文。
- 如需保留专业术语，优先采用“中文 + English term”的写法。
- 修改现有英文项目时，如用户没有要求整体翻译，允许保留原有英文标识、API 名、代码变量名和命令。

## 大模型调用配置

如果项目需要调用大模型，默认使用 OpenAI 兼容接口，并从环境变量读取配置：

```env
OPENAI_API_KEY=<从本地环境变量读取，不写入仓库或文档明文>
OPENAI_BASE_URL=https://ai.12zx.net/v1
OPENAI_API_MODE=chat
OPENAI_MODEL=gpt-5.4
OPENAI_INPUT_PRICE_PER_1M=0
OPENAI_OUTPUT_PRICE_PER_1M=0
```

实现代码时不要把 `OPENAI_API_KEY` 硬编码到源码、README、Prompt 模板或测试文件中。
