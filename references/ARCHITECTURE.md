# ThinkStack 架构速查（ARCHITECTURE.md）

> 从 `E:\PC\ThinkStack` 源码（v1.1.0）提炼，供 TSA-skill 运行时精确引用。
> Distilled from ThinkStack source v1.1.0 for accurate in-skill reference.

## 模块结构与依赖方向

| 层 | 模块 | 核心职责 | 依赖 |
|----|------|----------|------|
| Core | `thinkstack.config` | `Config` 聚合配置 | 无 |
| Core | `thinkstack.errors` | `ThinkStackError` 异常体系 | 无 |
| Core | `thinkstack.core.agent` | `Agent` 基类、`think→act→observe` 循环 | Tool, Memory, Reasoner |
| Core | `thinkstack.core.tool` | `Tool` / `FunctionTool` / `ToolResult` / `tool` 装饰器 | errors |
| Core | `thinkstack.core.memory` | `Short/Long/WorkingMemory` | errors |
| Core | `thinkstack.core.scheduler` | `Serial/Parallel/PriorityScheduler`、`Task` | errors |
| Core | `thinkstack.core.reasoner` | `Reasoner` 抽象 + `EchoReasoner` | 无 |
| Core | `thinkstack.core.stack` | `ThinkStack` 主入口 | 以上全部 + expand |
| Core | `thinkstack.core.agents` | `EchoAgent` / `ToolCallingAgent` / `MarkdownAgent` | agent |
| Core | `thinkstack.core.markdown` | `markdown_to_html()`（纯标准库） | 无 |
| Expand | `thinkstack.expand.hooks` | `ExpandHook` 枚举（10 点） | 无 |
| Expand | `thinkstack.expand.handle` | `ExtensionHandle` | errors |
| Expand | `thinkstack.expand.api` | `@expand_hook` + `register_extension` + `ExtensionRegistry` | hooks, loader |
| Expand | `thinkstack.expand.loader` | `ExtensionLoader`（importlib 安全加载） | hooks, errors |
| Runtime | `thinkstack.runtime.server` | `ThinkStackServer`（9635 REST） | stack |
| Runtime | `thinkstack.runtime.webconsole` | `WebConsole`（`webrun <port>`，浅/深色） | stack |

## 关键类型签名

### `ThinkStack`
```python
ThinkStack(config: Config | None = None)
.start() -> None
.shutdown() -> None
.is_running -> bool
.run_agent(agent: Agent, task_input, max_iterations: int | None = None) -> AgentResult
.run_agent_stream(agent, task_input, max_iterations=None) -> Iterator[dict]
.register_tool(tool: Tool) -> None
.call_tool(name: str, **kwargs) -> ToolResult
.acall_tool(name: str, **kwargs) -> ToolResult          # 异步
.list_tools() -> list[dict]
.store_long_term(key, value) / retrieve_long_term(key, default=None)
.store_short_term(key, value) / retrieve_short_term(key, default=None)
.store_working(key, value) / retrieve_working(key, default=None)
.get_memory(kind: "long"|"short"|"working")
.submit_task(task: Task) / run_tasks() -> list[TaskResult]
.register_agent(name: str, agent) -> None               # Agent 实例或子类
.resolve_agent(name: str) -> Agent | None
.list_agents() -> list[str]
.register_extension(name: str, module_path: str) -> ExtensionHandle
.list_extensions() -> list[ExtensionHandle]
.get_extension(name: str) -> ExtensionHandle
```

### `Agent`（抽象基类）
```python
Agent(name: str | None = None, reasoner: Reasoner | None = None)
.think(context: dict) -> str            # 抽象，必须覆写
.act(thought: str) -> Any               # 抽象
.observe(action: Any) -> Any            # 抽象
.should_stop(observation) -> bool       # 默认 False
.run(task_input, max_iterations=10) -> AgentResult   # 不触框架钩子
# 内置: EchoAgent, ToolCallingAgent, MarkdownAgent（均来自 thinkstack.core.agents）
```

### `Tool` / `FunctionTool` / `tool`
```python
FunctionTool(name: str, description: str, func: Callable,
             input_schema: type[BaseModel] = EmptyInput, is_async: bool = False)
ToolResult.ok(data) -> ToolResult
ToolResult.fail(error: str) -> ToolResult
# 装饰器：
@tool(name=None, description="", input_schema=EmptyInput, is_async=False)
def my_func(...) -> ...: ...
```

### `Memory`
```python
ShortTermMemory(capacity: int = 100)        # 会话级
LongTermMemory 子类: InMemoryLongTermMemory(), JsonFileLongTermMemory(path="thinkstack_memory.json")
WorkingMemory()                             # 临时上下文
# 接口: store(key, value) / retrieve(key, default=None) / clear()
```

### `Scheduler`
```python
SerialScheduler()
ParallelScheduler(max_workers: int = 4)
PriorityScheduler()
# Task(name, func, priority: int = 0, args=(), kwargs={})
# scheduler.submit(task) / scheduler.run_all() -> list[TaskResult]
```

### `Reasoner`（模型无关核心）
```python
class Reasoner(ABC):
    name: str
    def reason(self, context: dict, instruction: str = "") -> str: ...   # 抽象

class EchoReasoner(Reasoner):   # 占位实现，不依赖任何模型
    def reason(self, context, instruction="") -> str: ...
```
> **接入真实模型：只实现 `Reasoner` 子类**，注入任意 Agent 即可，框架其余部分零改动。

### `Config`
```python
Config(
  name="ThinkStack", agent_name="default-agent", max_iterations=10,  # 1..1000
  memory=MemoryConfig(short_term_capacity=100,
                      long_term_backend="in_memory"|"json_file",
                      persist_path=""),
  scheduler=SchedulerConfig(strategy="serial"|"parallel"|"priority", max_workers=4),
  server=ServerConfig(host="0.0.0.0", port=9635, enable_console_command=True),
  log=LogConfig(level="INFO", file=""),
)
Config.from_dict({...}) -> Config      # 校验构造，非法抛 ConfigError
```

### Expand API
```python
# 装饰器：把函数挂到扩展点
@expand_hook(ExpandHook.HOOK_CUSTOM_TOOL)        # func() -> Tool
@expand_hook(ExpandHook.HOOK_CUSTOM_MEMORY)      # func() -> LongTermMemory
@expand_hook(ExpandHook.HOOK_CUSTOM_SCHEDULER)   # func() -> Scheduler
@expand_hook(ExpandHook.HOOK_CUSTOM_AGENT)        # func() -> Agent(类或实例)
@expand_hook(ExpandHook.HOOK_BEFORE_THINK)        # func(ctx: dict) -> dict
# ... HOOK_AFTER_THINK / BEFORE_ACTION / AFTER_ACTION /
#     BEFORE_OBSERVE / AFTER_OBSERVE 同签名 func(ctx)->dict

register_extension(name: str, module_path: str) -> ExtensionHandle   # 默认注册表
ExtensionHandle.enable() / .disable() / .unload()  + 只读 .is_active
```

## REST API（9635 端口）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/info` | 框架信息 |
| POST | `/api/agent/run` | 运行 agent（body: `{"agent","input","max_iterations"}`） |
| POST | `/api/agent/run/stream` | SSE 流式运行 |
| POST | `/api/tools/call` | 调用工具（body: `{"name","args"}`） |
| POST | `/api/markdown/render` | Markdown→HTML（body: `{"text"}`） |
| POST | `/api/memory` | 读写记忆（body: `{"action","kind","key","value"}`） |
| POST | `/api/command` | 命令通道，支持 `{"command":"webrun 8080"}` 开 Web 控制台 |

## CLI
```bash
python run.py                       # 启动 9635 REST
python -m thinkstack               # 等价
python -m thinkstack --port 9000   # 指定端口
python -m thinkstack --repl        # 交互 REPL（英文输出：echo/md/tool/help/exit）
python -m pytest -v                # 44 个单元测试
```
