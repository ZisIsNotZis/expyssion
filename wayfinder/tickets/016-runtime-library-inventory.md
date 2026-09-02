---
id: 016
title: "Runtime library inventory and collector edge cases"
labels: [wayfinder:grilling]
status: closed
assignee: z
blocked-by: ["010"]
---

## Question

Fix the exact v1 runtime function set and their contracts, now that the channel (001), generator semantics (002), and protocol shape (010) are settled: the control structures (`if/while/for/try/raise/return/break/continue` internal forms), collectors (`list/dict/set` edge cases — nested collection, wrong-shape yields for dict/set, mixed yielding/non-yielding arguments), the `generator` wrapper details, Python-side iteration interop, the sequence family (`zip/range/map/filter/first/...`), delegation (`yield from` equivalent or its absence), and which Python builtins are re-exported as-is. Deliverable: the v1 library table the spec's standard-library section is written from.

**Resolution (closed 2025-09-01, auto-run):** the v1 table. **Control structures:** `if c t (e?)` — else optional, absent else yields null; **branches are invoked callables, literal branches wrapped as thunks `(:v)`**; `while cond body (else?)` — cond is a lambda re-invoked per iteration (the doc's `(:x)` footnote remains correct under call-by-value); `for iter body (else?)` — body is a one-param lambda (the element) or zero-param; for/while return the last body value, else runs on completion-without-break; `try body handler` — handler receives the exception, re-raise via `raise`; no finally (use `with_resource`); `raise exc` requires an exception instance (non-exception → TypeError, Python parity). **Collectors:** list/dict/set per ticket 002; dict consumes key-value 2-sequences, wrong shape → loud error. **Sequences/helpers:** range, zip, len, map (lazy), filter (lazy), first, sorted, enumerate, reversed, sum, min, max, abs, print, str/int/float, isinstance, getattr; subscript reads `xs[i]` and slices `xs[i:j]` in the grammar. **Modules:** `import name` binds the module object; alias by assignment. **Re-export policy:** the curated list above; everything else reached by attribute access on imported modules. **Delegation:** none in v1 (per ticket 002).

**Amendment (owner decision, 2025-09-01):** call sites support **kwargs via `name:=value`** — very high precedence, no parens needed (`connect "example.com" port:= 8080`); extras collected by `...`; kwargs after positionals, Python order. Library functions are positional-first but kwargs work everywhere. Non-callable invocation = native TypeError (ticket 014). Negative numbers: `-1` is a literal token; expression negation via `0- x` or the library function `neg`. **No `floor_div` helper — floor division is `int a/b`** (arithmetic infix binds tighter than the argument boundary; `int` is the ordinary int function). No generics for now.

**Amendment (owner review, 2025-09-01):** no `//` — floor division via a library function; `**` kept (no single-symbol alternative); slices via the constructor `xs[slice a b]` (no slice syntax); no comma/tuple syntax — multi-values are lists (`list 3 4`), destructuring `(a b)= list 3 4`; dict construction via collectors yielding 2-lists (`yield list k v`); no augmented operators (ticket 003); the `generator` wrapper does not exist (ticket 002 — consumers drive yielding lambdas directly).
