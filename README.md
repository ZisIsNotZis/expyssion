<p align="center"><img src="docs/logo.svg" alt="expyssion" width="460"></p>

# expyssion

**A Python-hosted language with no keywords: `if`, `while`, `for`, `try` and `yield` are ordinary functions, so `yield` and `return` cross lambda boundaries.**

Everything is an expression; everything is a call. There are no special forms — the only hard-wired syntax is `=` (assignment) and `:` (lambda), and every other name, including the control structures, can be shadowed. `LANGUAGE.md` is the frozen v1 reference; the tree-walking Python interpreter implements it literally on greenlets.

```expy
# fibonacci — `if` takes callables, so literal branches are thunks
febonacci= n: if n<= 1 (: n) (: (febonacci n- 1)+ febonacci n- 2)
print (febonacci 10)
```

```text
55
```

The distinctive part is what crosses calls: a yielding lambda *is* a generator, and any consumer drives it — no generator type, no `yield from`, no depth parameter.

```expy
nums= :
  for (range 100) x:
    yield x
list (for nums x:
  if x%3== 0 (: yield x* x)
)
```

`list` drives the lambda and collects `[0, 9, 36, 81, …]` — 34 values.

## Quick start

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```sh
git clone git@github.com:ZisIsNotZis/expyssion.git
cd expyssion
uv sync --group dev
uv run expy tests/programs/febonacci.expy   # prints 55
uv run pytest                               # 95 tests
```

Without uv, install into a Python environment:

```sh
python -m pip install .
expy tests/programs/febonacci.expy
```

`expy run <file.expy>` and `expy <file.expy>` are the same command; `expy --help` prints the usage line.

The three programs in [`tests/programs/`](tests/programs/) are the end-to-end fixtures — a recursion/thunk example (`febonacci.expy`), a generator pipeline (`pipeline.expy`), and early return through an `if` branch (`guard.expy`).

## Why it is shaped this way

- **One form.** `f a b` is `f(a, b)`; indentation passes arguments to the last token on the line; there are no statements, only expressions.
- **Control flow is a library.** `if c t e` invokes its branches; `while` re-invokes its condition lambda; `for` drives an iterable *or* a yielding lambda. Pass `(: v)` for a literal value.
- **Effects cross frames.** Every call runs as-if at a sync point on a fresh greenlet (ADR 0001). `yield` suspends the chain and is caught by the nearest collector; `return` bubbles to the nearest lambda born from `=`; loop drivers catch `break`/`continue`.
- **Python underneath.** Literals, truthiness and f-strings are Python's; any Python callable is callable; `import "numpy"` binds the module. Cleanup is driver-owned: on break, error or close the driver injects `GeneratorExit` so `finally` runs.
- **Loud errors.** Unhandled yield, escaped return, and break/continue outside a loop raise named errors instead of silently misbehaving.

## Status

Closed milestone (2026-09-29). v1 is complete; no further development is planned unless the inputs or goals change.

| | |
|---|---|
| **Done** | `LANGUAGE.md` v1 spec; lexer, parser, sync-point machine, evaluator and stdlib; `expy` CLI; 95 passing tests; two ADRs; 16 resolved design tickets |
| **Not done** | Broader stdlib, a second runtime, performance work (an M2 elision/compilation path is designed but unbuilt), asyncio (the language is deliberately blocking) |
| **Next** | None planned |

Details and evidence: [`docs/project-status.md`](docs/project-status.md).

## Documentation map

| Document | What it settles |
|---|---|
| [`LANGUAGE.md`](LANGUAGE.md) | The v1 language reference: syntax, semantics, execution model, stdlib, errors |
| [`CONTEXT.md`](CONTEXT.md) | Glossary of the language's terms |
| [`docs/transpilation.md`](docs/transpilation.md) | Semantic-equivalence corpus: each construct beside its plain-Python meaning, with a runnable oracle (`docs/verify_corpus.py`) |
| [`docs/adr/`](docs/adr/) | Why the machine is sync-point based (0001) and why v1 is an interpreter, not a transpiler (0002) |
| [`wayfinder/`](wayfinder/) | The design record: destination, 16 tickets, substrate research on greenlet |
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
