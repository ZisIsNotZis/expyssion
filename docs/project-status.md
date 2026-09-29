# expyssion project status

## Classification

Closed language milestone: a Python-hosted expression language where everything
is an expression and everything is a call.

## Status

Closed as a milestone (2026-09-29). The v1 destination — a self-consistent
`LANGUAGE.md` spec plus a working implementation — is reached. No further
development is planned unless the project's inputs or goals change.

## Evidence

- Spec: [`../LANGUAGE.md`](../LANGUAGE.md) (v1), with grammar, semantics, and the
  Python-transpilation story; rationale in [`adr/`](adr/).
- Implementation: `src/` (lexer, parser, sync-point machine on greenlets,
  evaluator, stdlib) and the `expy` CLI.
- Tests: `tests/` — `uv run pytest` (95 passed on 2026-09-29).
- Design record: [`../wayfinder/`](../wayfinder/) — 16 tickets resolved.

## Deferred

The wayfinder map's destination was explicitly "spec only" for v1; broader
library coverage, additional runtimes, and polish beyond the frozen spec were
left as future work.
