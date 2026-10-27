[English](README.md) · 简体中文

<p align="center"><img src="docs/logo.svg" alt="expyssion" width="460"></p>

# expyssion

**一切都是表达式，一切都是调用。**

**一门托管在 Python 上的语言：控制结构就是普通函数——`yield` 与 `return` 能跨 lambda 边界，没有关键字、没有生成器类型，也不需要 depth 参数。**

`if`、`while`、`for`、`try` 和 `yield` 都是接收可调用对象的库函数。硬编码的语法只有 `=`（赋值）和 `:`（lambda），其余名字——包括控制结构——都可以被遮蔽。一个树遍历解释器运行在 greenlet 的同步点效果机之上，逐条实现已冻结的 v1 规范。

## 快速开始

需要 Python 3.12+ 与 [uv](https://docs.astral.sh/uv/)。

```sh
git clone https://github.com/ZisIsNotZis/expyssion.git
cd expyssion
uv sync --group dev
uv run expy tests/programs/febonacci.expy   # 输出 55
uv run pytest                               # 完整测试套件
```

不用 uv 时，可以直接安装到 Python 环境：

```sh
python -m pip install .
expy tests/programs/febonacci.expy
```

`expy run <file.expy>` 与 `expy <file.expy>` 等价；`expy --help` 会打印用法。

## 现在能做什么

用 thunk 分支写斐波那契——`if` 调用的是可调用对象，所以字面量分支要写成 `(: …)`：

```expy
febonacci= n: if n<= 1 (: n) (: (febonacci n- 1)+ febonacci n- 2)
print (febonacci 10)
```

```text
55
```

会 yield 的 lambda 本身就是生成器；`list` 负责驱动并收集结果。没有生成器类型，没有 `yield from`，也没有 depth 参数：

```expy
nums= :
  for (range 100) x:
    yield x
list (for nums x:
  if x%3== 0 (: yield x* x)
)
```

`list` 收集到 `[0, 9, 36, 81, …]`，共 34 个值。

目前可用的能力：

| 能力 | 实际含义 |
|---|---|
| 一等公民的控制流 | `if`/`while`/`for`/`try` 都是普通函数；字面量分支用 `(: v)` 包装 |
| 跨帧的效果 | `yield` 挂起调用链并由最近的收集器捕获；`return`、`break`、`continue` 可以跨 lambda 边界 |
| 生成器与推导式 | 会 yield 的 lambda 可交给 `list`、`dict`、`set`、`for` 使用——嵌套收集器同样成立 |
| Python 互操作 | 任何 Python 可调用对象都能调用；`import "numpy"` 绑定模块；`for` 能遍历 Python 可迭代对象 |
| 名字可遮蔽 | `if`、`list` 等内建名字都能重新绑定；只有 `=` 和 `:` 是保留语法 |
| 响亮的失败 | 未处理的 yield、逃逸的 return、循环外的 break/continue 都会抛出有名字的错误 |
| CLI 与 API | `expy` 运行 `.expy` 文件；`run_source` / `run_file` 可嵌入解释器 |

[`tests/programs/`](tests/programs/) 里的三个端到端样例分别覆盖递归与 thunk、生成器管道、以及在 `if` 分支中提前返回。

## 架构

源码先经词法分析器和语法分析器生成 AST，再由求值器执行。每次调用 expyssion lambda 都视作在全新 greenlet 的同步点上运行（ADR 0001），帧之间通过控制消息传递效果。原生 Python 可调用对象直接调用，因此导入和 C 代码保持原子性。

| 层 | 文件 | 职责 |
|---|---|---|
| 语法 | `src/expyssion/lexer.py`、`parser.py`、`nodes.py` | 缩进感知的词法单元、表达式解析器、AST 节点 |
| 求值 | `src/expyssion/evaluator.py`、`env.py`、`stdlib.py` | 树遍历求值器、词法环境、内建库 |
| 机器 | `src/expyssion/machine.py` | greenlet 同步点效果机：spawn、yield/resume、return、close |
| 入口 | `src/expyssion/api.py`、`cli.py` | `run_source` / `run_file` 与 `expy` 命令 |
| 错误 | `src/expyssion/errors.py` | `ExpyssionError` 与响亮错误的词汇表 |

执行模型是规范性的，解释器只是它的一种实现。ADR 0001 记录了这套机器及其代价，ADR 0002 记录了为什么选择 AST 解释而非转译。完整语义见 [`LANGUAGE.md`](LANGUAGE.md)。

## 开发方式

```sh
uv sync --group dev
uv run pytest
uv run python docs/verify_corpus.py   # 语义等价语料
```

- 规范是唯一事实来源：修改 `LANGUAGE.md` 时要同步更新语料。
- 设计记录在 [`wayfinder/`](wayfinder/)；取舍理由写在 [`docs/adr/`](docs/adr/)。
- 用 `uv run expy <file.expy>` 运行程序；单元测试和端到端测试在 [`tests/`](tests/)。

## 参与贡献

见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。v1 是一个已关闭的里程碑：缺陷修复、测试和文档修正都欢迎；语言或语义层面的改动请先开 issue，并走设计记录流程。

## 路线图

**已实现**

- `LANGUAGE.md` v1 规范：语法、语义、执行模型、标准库、错误
- 可用的解释器：缩进感知词法分析器、语法分析器、求值器、greenlet 同步点机器、标准库
- `expy` CLI，以及可嵌入的 `run_source` / `run_file` API
- 95 个通过的测试，以及三个端到端 `.expy` 样例
- [`docs/transpilation.md`](docs/transpilation.md) 中的语义等价语料，由 `docs/verify_corpus.py` 校验
- [`wayfinder/`](wayfinder/) 中的两份 ADR 与 16 个已解决设计工单

**计划中**

- 当前目标下没有计划项。v1 已于 2026-09-29 关闭。

除非目标改变，否则明确不做：M2 省略/编译快速路径（已有设计、尚未实现）、更广的标准库、第二套运行时，以及 asyncio（这门语言刻意保持阻塞语义）。

**未来设想**

expyssion 是一次小实验：把关键字层整个拿掉。如果控制结构只是函数，那么生成器、提前返回和推导式收集器都从同一套执行模型里自然长出来，而不是各自成为独立的语言特性。如果继续开发，下一步是保持同步点语义不变的 M2 编译路径——更快，但不改变程序的含义。结项证据见 [`docs/project-status.md`](docs/project-status.md)。

## 文档

| 文档 | 内容 |
|---|---|
| [`LANGUAGE.md`](LANGUAGE.md) | v1 语言参考：语法、语义、执行模型、标准库、错误 |
| [`CONTEXT.md`](CONTEXT.md) | 语言术语表 |
| [`docs/transpilation.md`](docs/transpilation.md) | 语义等价语料：每个构造及其对应的普通 Python 含义 |
| [`docs/adr/`](docs/adr/) | 为什么采用同步点机器（0001），为什么 v1 是解释器（0002） |
| [`wayfinder/`](wayfinder/) | 设计地图、16 个工单、greenlet 底座研究 |
| [`docs/project-status.md`](docs/project-status.md) | 结项状态与证据 |

## 仓库结构

```text
src/expyssion/   词法分析器、语法分析器、greenlet 机器、求值器、标准库、CLI
tests/           单元测试、端到端 CLI 测试、.expy 样例
docs/            ADR、证明语料、logo、项目状态
wayfinder/       设计地图、工单、greenlet 研究
LANGUAGE.md      冻结的 v1 规范
```

## 许可证

[AGPL-3.0-only](LICENSE)。
