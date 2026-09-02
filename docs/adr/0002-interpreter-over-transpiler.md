# ADR 0002 — AST interpreter over source-to-source transpiler

## Status

Accepted (2025-09-02, owner decision during implementation planning)

## Context

LANGUAGE.md v1 defined expyssion semantics normatively as the sync-point effect machine and framed the implementation as "transpiles to Python", with elision as a pure optimization. The proof corpus (docs/transpilation.md) showed readable elided Python per construct. Implementation planning had to choose the actual execution strategy.

## Decision

Implement expyssion as an **AST tree-walking interpreter hosted on Python**, which implements the sync-point machine literally: every invocation of an expyssion lambda runs in a fresh greenlet; `yield` performs a direct parent-switch (the greenlet's frozen stack is the resumable frame); `return`/`break`/`continue` are BaseException subclasses caught by assigned frames and loop drivers respectively. No Python source is emitted.

Consequences folded into this decision:

- **M1 scope**: every expyssion-lambda call goes through the machine (no elision); native Python callables are invoked directly (they cannot yield, so no sync point is needed — consistent with the as-if clause). Elision becomes an M2 interpreter-level optimization, guarded by the same corpus.
- **Corpus repositioned**: docs/transpilation.md is a *semantic-equivalence reference* ("what each construct means in plain Python"), not compiler output. Its executable checks (docs/verify_corpus.py) remain the behavioral oracle.
- **Interop shell**: expyssion lambdas exposed to Python are wrapper objects (`__call__` runs a plain machine call — an escaping yield becomes the loud unhandled-yield error, so yields never cross native frames; `__iter__` drives the lambda for Python consumers).
- **Scoping is ours**: environments form a lexical parent chain; assignment walks ancestors to edit bindings (auto cells), else defines locally; parameters shadow. Python's own scoping rules do not participate.

## Alternatives considered

- **Source-to-source transpiler** (emit readable .py): rejected — the correctness burden shifts to code generation (f-strings, name mangling, walrus placement, the `_e.` emission path), for no performance need in a personal language; the corpus promise of readable output would also make M1 partial.
- **Direct bytecode / code-object generation**: rejected — same burden, more opacity, zero benefit at this scale.

## Consequences

- The identity line in LANGUAGE.md changes from "transpiles to Python" to Python-hosted interpretation; the name "expression py" keeps its meaning (Python semantics, Python ecosystem).
- Recursion/chain depth is bounded by CPython's recursion limit inside each greenlet stack; the machine raises documented limits (see substrate facts).
- Performance is interpreter-grade; the design keeps the door open to an M2 compiling fast path without semantic change, since the machine remains normative.
