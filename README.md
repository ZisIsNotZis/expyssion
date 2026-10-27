English · [简体中文](README.zh-CN.md)

<p align="center"><img src="docs/logo.svg" alt="expyssion" width="460"></p>

# expyssion

**Everything is an expression; everything is a call.**

**A Python-hosted language where control flow is ordinary functions — `yield` and `return` cross lambda boundaries, with no keywords, no generator type, and no depth parameter.**

`if`, `while`, `for`, `try` and `yield` are library functions taking callables. The only hard-wired syntax is `=` (assignment) and `:` (lambda), and every other name — including the control structures — can be shadowed. A tree-walking interpreter implements the frozen v1 spec literally as a sync-point effect machine on greenlets.

## Quick start

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```sh
git clone https://github.com/ZisIsNotZis/expyssion.git
cd expyssion
uv sync --group dev
uv run expy tests/programs/febonacci.expy   # prints 55
uv run pytest                               # full suite
```

Without uv, install into a Python environment:

```sh
python -m pip install .
expy tests/programs/febonacci.expy
```

`expy run <file.expy>` and `expy <file.expy>` are the same command; `expy --help` prints the usage line.

## What it can do now

Fibonacci with thunk branches — `if` invokes callables, so literal branches are wrapped in `(: …)`:

```expy
febonacci= n: if n<= 1 (: n) (: (febonacci n- 1)+ febonacci n- 2)
print (febonacci 10)
```

```text
55
```

A yielding lambda *is* the generator; `list` drives it and collects the values. No generator type, no `yield from`, no depth parameter:

```expy
nums= :
  for (range 100) x:
    yield x
list (for nums x:
  if x%3== 0 (: yield x* x)
)
```

`list` collects `[0, 9, 36, 81, …]` — 34 values.

Working today:

| Capability | What it means in practice |
|---|---|
| First-class control flow | `if`/`while`/`for`/`try` are ordinary functions; pass `(: v)` for a literal branch |
| Effects across frames | `yield` suspends the chain to the nearest collector; `return`, `break` and `continue` cross lambda boundaries |
| Generators and comprehensions | A yielding lambda is consumed by `list`, `dict`, `set`, `for` — nested collectors work |
| Python interop | Any Python callable is callable; `import "numpy"` binds the module; `for` consumes Python iterables |
| Shadowable names | Rebind `if`, `list` or any other builtin; only `=` and `:` are reserved |
| Loud failures | Unhandled yield, escaped return, and loop control outside a loop raise named errors |
| CLI and API | `expy` runs `.expy` files; `run_source` / `run_file` embed the interpreter |

The three end-to-end fixtures in [`tests/programs/`](tests/programs/) exercise recursion and thunks, a generator pipeline, and early return through an `if` branch.

## Architecture

Source text flows through a lexer and parser into an AST, which the evaluator executes. Every expyssion-lambda invocation runs as-if at a sync point on a fresh greenlet (ADR 0001); effects travel between frames as control messages. Native Python callables are called directly, which is why imports and C code stay atomic.

| Layer | Files | Role |
|---|---|---|
| Syntax | `src/expyssion/lexer.py`, `parser.py`, `nodes.py` | Indentation-aware tokens, expression parser, AST nodes |
| Evaluation | `src/expyssion/evaluator.py`, `env.py`, `stdlib.py` | Tree-walking evaluator, lexical environments, builtin library |
| Machine | `src/expyssion/machine.py` | Greenlet sync-point machine: spawn, yield/resume, return, close |
| Entry points | `src/expyssion/api.py`, `cli.py` | `run_source` / `run_file` and the `expy` command |
| Errors | `src/expyssion/errors.py` | `ExpyssionError` and the loud-error vocabulary |

The execution model is normative; the interpreter is one implementation of it. ADR 0001 records the machine and its trade-offs, ADR 0002 records the choice of AST interpretation over transpilation. The full semantics are in [`LANGUAGE.md`](LANGUAGE.md).

## How to develop

```sh
uv sync --group dev
uv run pytest
uv run python docs/verify_corpus.py   # semantic-equivalence corpus
```

- The spec is the source of truth: change `LANGUAGE.md` and the corpus together.
- The design record lives in [`wayfinder/`](wayfinder/); rationale belongs in [`docs/adr/`](docs/adr/).
- Run programs with `uv run expy <file.expy>`; unit and end-to-end tests live in [`tests/`](tests/).

## How to contribute

See [`CONTRIBUTING.md`](CONTRIBUTING.md). v1 is a closed milestone: bug fixes, tests and documentation corrections are welcome, while language or semantics changes should start as an issue and go through the design record.

## Roadmap

**Implemented**

- `LANGUAGE.md` v1 spec: grammar, semantics, execution model, standard library, errors
- Working interpreter: indentation-aware lexer, parser, evaluator, greenlet sync-point machine, stdlib
- `expy` CLI plus the embeddable `run_source` / `run_file` API
- Test suite with 95 passing tests and three end-to-end `.expy` fixtures
- Semantic-equivalence corpus in [`docs/transpilation.md`](docs/transpilation.md), checked by `docs/verify_corpus.py`
- Two ADRs and 16 resolved design tickets in [`wayfinder/`](wayfinder/)

**Planned**

- None under the current goal. v1 is closed as of 2026-09-29.

Explicitly not planned unless the goal changes: an M2 elision/compilation fast path (designed in language, unbuilt), broader standard-library coverage, a second runtime, and asyncio support (the language is deliberately blocking).

**Future vision**

expyssion is a small experiment in removing the keyword layer entirely: if control flow is just functions, then generators, early returns and comprehension collectors all fall out of one execution model instead of being separate language features. If development resumes, the next step is an M2 compiled path that preserves the same sync-point semantics — faster, with no change to what programs mean. See [`docs/project-status.md`](docs/project-status.md) for close-out evidence.

## Documentation

| Document | What it settles |
|---|---|
| [`LANGUAGE.md`](LANGUAGE.md) | The v1 language reference: syntax, semantics, execution model, stdlib, errors |
| [`CONTEXT.md`](CONTEXT.md) | Glossary of the language's terms |
| [`docs/transpilation.md`](docs/transpilation.md) | Semantic-equivalence corpus: each construct beside its plain-Python meaning |
| [`docs/adr/`](docs/adr/) | Why the machine is sync-point based (0001) and why v1 is an interpreter (0002) |
| [`wayfinder/`](wayfinder/) | Design map, 16 tickets, greenlet substrate research |
| [`docs/project-status.md`](docs/project-status.md) | Close-out status and evidence |

## Repository layout

```text
src/expyssion/   lexer, parser, greenlet machine, evaluator, stdlib, CLI
tests/           unit tests, end-to-end CLI tests, .expy fixtures
docs/            ADRs, proof corpus, logo, status
wayfinder/       design map, tickets, greenlet research
LANGUAGE.md      frozen v1 specification
```

## License

[AGPL-3.0-only](LICENSE).
