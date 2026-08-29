#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scaffold_agent_app.py — Generate a ThinkStack-based agent app skeleton.

Creates a ready-to-run project that builds on the ThinkStack architecture
(https://github.com/Developerprit/ThinkStack.git). The generated code follows
the "everything is a writable extension" philosophy: a custom tool extension is
wired in via the ThinkStack Expand API, and an Agent runs through the standard
think->act->observe loop.

Usage:
    python scaffold_agent_app.py --name my_agent_app
    python scaffold_agent_app.py --name demo --out ./build --agent tool

Output layout:
    <out>/<name>/
        app.py                  # entry: ThinkStack + extension + run_agent
        extensions/greet_tool.py # sample HOOK_CUSTOM_TOOL extension
        pyproject.toml
        requirements.txt
        README.md               # bilingual (zh / en)

CLI output is English (per project convention).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

APP_TEMPLATE = '''\
# -*- coding: utf-8 -*-
"""[{name}] application entry — built on ThinkStack.

Follows the "everything is a writable extension" architecture:
- extensions are plain .py files marked with @expand_hook
- the framework is assembled via ThinkStack(config) -> register_extension -> start
"""
from thinkstack import ThinkStack, EchoAgent, Config


def build_config() -> Config:
    return Config(
        name="{name}",
        max_iterations=5,
        # memory: "in_memory" | "json_file"  (json_file persists to disk on shutdown)
        memory={{"long_term_backend": "in_memory"}},
        # scheduler: "serial" | "parallel" | "priority"
        scheduler={{"strategy": "serial"}},
        server={{"port": 9635}},
    )


def main() -> None:
    stack = ThinkStack(build_config())

    # Register a custom tool extension (loads examples/greet_tool.py).
    # To add more capabilities, drop another @expand_hook file and register it.
    stack.register_extension("greet", "extensions/greet_tool.py")

    stack.start()

    # Quick self-check: call the extension tool.
    result = stack.call_tool("greet", name="陌老师")
    print("[tool] greet ->", result.data)

    # Run a built-in agent through the think->act->observe loop.
    agent_result = stack.run_agent(EchoAgent(), "你好，ThinkStack", max_iterations=2)
    print("[agent] output ->", agent_result.output)
    print("[agent] iterations ->", agent_result.iterations)

    # Expose an HTTP service instead? Just run:  python run.py  (port 9635)
    # Open a light/dark web console?  send command:  webrun 8080
    stack.shutdown()


if __name__ == "__main__":
    main()
'''

EXTENSION_TEMPLATE = '''\
# -*- coding: utf-8 -*-
"""Sample extension: a custom "greet" tool (HOOK_CUSTOM_TOOL).

Demonstrates tool registration + pydantic input validation via the
ThinkStack Expand API. Drop more of these and register them in app.py.
"""
from pydantic import BaseModel, Field

from thinkstack import ExpandHook, FunctionTool, expand_hook


class GreetInput(BaseModel):
    name: str = Field(description="Name to greet")


@expand_hook(ExpandHook.HOOK_CUSTOM_TOOL)
def register_greet_tool() -> FunctionTool:
    return FunctionTool(
        name="greet",
        description="Return a friendly greeting for the given name",
        input_schema=GreetInput,
        func=lambda name: f"Hello, {{name}}! (from ThinkStack extension)",
    )
'''

PYPROJECT_TEMPLATE = '''\
[project]
name = "{name}"
version = "0.1.0"
description = "Agent application built on the ThinkStack architecture"
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2.0",
    "typing-extensions>=4.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0"]
'''

REQUIREMENTS_TEMPLATE = '''\
pydantic>=2.0
typing-extensions>=4.0
'''

README_TEMPLATE = '''\
# {name}

> Agent application built on the **ThinkStack** architecture.
> 基于 **ThinkStack** 架构开发的智能体应用。

ThinkStack: https://github.com/Developerprit/ThinkStack.git

## 特性 / Features
- 四层架构 + ThinkStack Expand API（一切皆为可编写的扩展）
- 模型无关：通过 `Reasoner` 抽象接入任意模型
- 内置 9635 REST API 与浅色/深色 Web 控制台

## 快速开始 / Quick start
```bash
pip install -r requirements.txt
# 确保 ThinkStack 可导入（本地优先，否则 git clone 仓库）
python app.py
# 启动 HTTP 服务：python run.py  (端口 9635)
# 开启控制台：webrun 8080
```

## 扩展 / Extend
新增能力只需写一个带 `@expand_hook` 的独立 .py 文件，并在 `app.py` 中
`register_extension(...)`。详见 ThinkStack 文档。

## License
Available License — https://license.kscm.top/available.md
'''


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold a ThinkStack-based agent application."
    )
    parser.add_argument("--name", required=True, help="Project / app name")
    parser.add_argument(
        "--out", default=".", help="Output directory (default: current dir)"
    )
    parser.add_argument(
        "--agent",
        default="echo",
        choices=["echo", "tool", "markdown"],
        help="Built-in agent to wire in the demo (default: echo)",
    )
    return parser.parse_args(argv)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  created: {path}")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    name = args.name
    root = Path(args.out) / name

    print(f"Scaffolding ThinkStack agent app: {name}")
    print(f"  target : {root.resolve()}")

    write_file(root / "app.py", APP_TEMPLATE.format(name=name))
    write_file(root / "extensions" / "greet_tool.py", EXTENSION_TEMPLATE)
    write_file(root / "pyproject.toml", PYPROJECT_TEMPLATE.format(name=name))
    write_file(root / "requirements.txt", REQUIREMENTS_TEMPLATE)
    write_file(root / "README.md", README_TEMPLATE.format(name=name))

    print("Done. Next steps:")
    print("  1) Ensure 'thinkstack' is importable (local copy or `git clone "
          "https://github.com/Developerprit/ThinkStack.git`).")
    print(f"  2) cd {name} && pip install -r requirements.txt && python app.py")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
