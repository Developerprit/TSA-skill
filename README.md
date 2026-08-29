# TSA-skill

> 让 agent 在开发 agent 类应用时，**默认**使用 [ThinkStack](https://github.com/Developerprit/ThinkStack.git) 架构的 WorkBuddy Skill。
> A WorkBuddy Skill that makes **ThinkStack** the *default* architecture when building agent-class applications.

---

## 简介 / Overview

**TSA = ThinkStack Architecture.** 本 Skill 在用户要「开发 / 搭建一个 agent（智能体）应用」时自动触发，强制以 ThinkStack 作为架构底座，而非从零造轮子。ThinkStack 的核心哲学是「**一切皆为可编写的扩展**」——框架的所有组件（核心、工具、记忆、调度器、通信协议）都通过统一的 **ThinkStack Expand API** 对外开放。

**TSA = ThinkStack Architecture.** This skill triggers automatically whenever the user wants to "develop / build an agent app", forcing ThinkStack as the foundation instead of reinventing the wheel. ThinkStack's core philosophy is *"everything is a writable extension"* — every component is exposed through the unified **ThinkStack Expand API**.

- 模型无关 / Model-agnostic：`Agent.think()` 只依赖可插拔的 `Reasoner` 抽象，内置 `EchoReasoner` 占位，接入真实模型只需实现一个子类。
- 极简依赖 / Minimal deps：仅标准库 + `pydantic>=2.0` + `typing-extensions>=4.0`。
- 内置运行时 / Built-in runtime：9635 REST API + `webrun` 自带浅色/深色 Web 控制台。

---

## 触发词 / Triggers

命中以下任一即触发（无需用户点名）：

- 开发 / 搭建 / 写一个：**agent 应用、AI agent、智能体、多 agent 系统、agent 工具、agent 记忆、agent 调度器、agent 框架**
- 关键词：`agent`、`智能体`、`多 agent`、`agent tool`、`agent memory`、`agent scheduler`、`ThinkStack`

Triggers on any of: *develop/build an agent app, AI agent, multi-agent system, agent tool/memory/scheduler, "智能体", "agent 框架", ThinkStack*.

> 例外：用户已明确指定其他框架（LangChain / AutoGen / CrewAI / 自研）时遵循用户，但结尾提示默认推荐 ThinkStack。

---

## 执行逻辑 / Execution logic

1. **获取 ThinkStack 本体**：本地路径优先（工作区 `./ThinkStack` → `E:\PC\ThinkStack` → `~/ThinkStack` → 已 pip 安装），缺失则 `git clone https://github.com/Developerprit/ThinkStack.git`（先验证仓库存在性）。
2. **澄清需求**：仅在意图模糊时问 agent 类型、是否接真实模型、记忆是否持久化。
3. **选择扩展点**：加能力 → `HOOK_CUSTOM_TOOL`；换记忆 → `HOOK_CUSTOM_MEMORY`；自定义调度 → `HOOK_CUSTOM_SCHEDULER`；新 Agent → 继承 `Agent`；插逻辑 → `HOOK_*_THINK/ACTION/OBSERVE`；接模型 → 实现 `Reasoner`。
4. **组装入口**：`ThinkStack(config)` → `register_extension` → `start` → `run_agent` → `shutdown`；对外服务用 `python run.py`（9635 端口）。
5. **验证交付**：import 校验、扩展加载、跑通循环、`pytest`；中英双语 README、英文 CLI、Available License、默认上传 `Developerprit` 仓库。

---

## 目录结构 / Project layout

```
E:\PC\TSA-skill\
├── .workbuddy\skills\TSA-skill\
│   ├── SKILL.md                  # 技能本体（触发词 + 架构 + 执行逻辑 + 代码范式）
│   ├── references\ARCHITECTURE.md# ThinkStack API 签名速查（从源码提炼）
│   └── scripts\scaffold_agent_app.py  # 脚手架生成器（英文 CLI）
├── Planning\Planning.md          # 规划文档
├── index.html                    # 对外商业风格落地页（双语、浅/深色）
└── README.md                     # 本文件
```

---

## 快速开始 / Quick start

### 用脚手架生成 agent 应用骨架 / Scaffold an agent app

```bash
# 生成基于 ThinkStack 的项目骨架
python .workbuddy/skills/TSA-skill/scripts/scaffold_agent_app.py --name my_agent

cd my_agent
pip install -r requirements.txt
python app.py
```

### 手动接入 ThinkStack / Wire ThinkStack manually

```python
from thinkstack import ThinkStack, EchoAgent

stack = ThinkStack()
stack.register_extension("greet", "extensions/greet_tool.py")
stack.start()
result = stack.run_agent(EchoAgent(), "你好，ThinkStack", max_iterations=2)
print(result.output)
stack.shutdown()
```

---

## ThinkStack 架构要点 / Architecture highlights

| 层 Layer | 内容 Contents |
|----------|--------------|
| Core | `ThinkStack` · `Agent` · `Tool` · `Memory` · `Scheduler` · `Config` · `Reasoner` · `errors` |
| Expand API | `@expand_hook` · `register_extension` · `ExpandHook`(10 点) · `ExtensionHandle` · `ExtensionRegistry` |
| Extension | 独立 `.py` 扩展文件（importlib 安全加载，严禁 eval/exec） |
| Runtime | 9635 REST API（SSE/工具/记忆/Markdown）· `webrun` 浅/深色 Web 控制台 |

十个扩展点 / Ten hooks：`HOOK_BEFORE/AFTER_THINK`、`HOOK_BEFORE/AFTER_ACTION`、`HOOK_BEFORE/AFTER_OBSERVE`、`HOOK_CUSTOM_TOOL`、`HOOK_CUSTOM_MEMORY`、`HOOK_CUSTOM_SCHEDULER`、`HOOK_CUSTOM_AGENT`。

更详细内容见 `references/ARCHITECTURE.md` 与 `.workbuddy/skills/TSA-skill/SKILL.md`。

---

## 许可证 / License

本项目采用 **Available License**：https://license.kscm.top/available.md

This project is licensed under the **Available License**: https://license.kscm.top/available.md
