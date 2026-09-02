# ADR 0001: Sync-point effect machine (S1⁺) as the language's execution model

Status: accepted · Date: 2025-09-01 · Decided during wayfinder charting

## Context

Expyssion is everything-is-a-call: `if/while/for/try` are ordinary functions taking callable arguments, so `return/break/continue/yield` must cross real lambda boundaries. Python's control flow is statement-based and its generators are stackless (lexical `yield`), so a pure-runtime design faces the colored-functions wall: `yield` cannot cross a runtime call boundary, and a user-specified frame `depth` makes generator identity undecidable.

## Decision

Adopt **S1⁺**: semantics are defined as a sync-point effect machine. Every expyssion call is (as-if) executed in a fresh greenlet with a sync point; effects travel as `Result<Yield|Err|Done>` messages with a `Resume` protocol; `yield` is a library-level effect — no depth parameter, no lexical generator marking for targeting, fully shadowable. Frame-crossing counts are compiler knowledge, never surface syntax. The compiler may elide sync points where the callee is provably pure (unshadowed builtin, no yield path) — a pure optimization that never changes observable semantics. Compiled output is a Python-hosted abstract machine (transpilation tier (b), accepted deliberately over the thin-skin tier (a)).

Rejected alternatives: S1-pure-runtime with exceptions and user/compiler depth (yield impossible across runtime calls, depth tax on everyday code); S2 special forms with inlining (zero machinery, readable output, but yield capped at Python's lexical rule and control structures not first-class); S3 shadowable special forms (semantic cliff under shadowing); S4 hybrid (two control-flow models).

## Consequences (con ledger, verified against greenlet 3.5.x docs)

- C-side compatibility: switches never occur inside C code, so numpy-style operations are atomic; callback seams (C→Python) cannot host yields — clean runtime error; re-entrancy caveat applies to C state held across suspension.
- GC: `GreenletExit` on last-reference-drop enables cleanup, but cycles involving greenlet frame data may not be collected — explicit close discipline is mandatory.
- asyncio is cut off (blocking world chosen); multiprocessing/pickling unsupported for lambdas; forking with suspended chains is hazardous.
- Standard tracing/profiling breaks at switches; tracebacks and error messages must be designed as a first-class feature.
- KeyboardInterrupt between protocol steps must be made exception-safe.
- Bonus that did not survive verification: recursion depth is **still bounded** by CPython's recursion limit — greenlet does not reset the per-thread counter across switches (verified empirically, see [research findings](../wayfinder/research/greenlet-runtime-facts.md)). The runtime must manage the limit; deep chains also produce concatenated tracebacks.
- Greenlet is a small C extension coupled to CPython internals (rewritten for 3.11; free-threading experimental) — thread-per-generator with the same protocol is the stdlib fallback.
