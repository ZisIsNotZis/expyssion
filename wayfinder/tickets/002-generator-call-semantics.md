---
id: 002
title: "Generator call semantics: marking, wrapper, or dynamic?"
labels: [wayfinder:grilling]
status: closed
assignee: z
blocked-by: []
---

## Question

When is calling a lambda a generator call (returns a lazy object) versus an ordinary call? The suspension target is already dynamic (nearest active handler, per ticket 001); only call semantics and handler identity need deciding.

**Motivating case (from ticket 001's session):** `[for (range 3) x: invoke (: yield x)]` — who receives the yield? Three candidate readings:

1. **No handler anywhere** → loud unhandled-yield error; the expression is Never.
2. **Lexical marking** (Python's rule: a lambda containing `yield` returns a generator object when called) → the list collects inert generator objects; nothing actually yields — marking makes yield "contagiously" lazy even when immediate yielding was intended.
3. **Collector-as-handler** — `list`/`dict`/`set` are effect handlers that collect each `Yield(v)` and answer `Resume`, giving `[0, 1, 2]`; comprehensions become pure library. Lazy Python-style generators come from an explicit `generator (lambda)` wrapper instead of implicit marking.

**Resolution (closed 2025-09-01):** Reading 3, with no lexical marking anywhere. `yield` behaves like a resumable exception: it propagates along the dynamic chain until someone catches it — comprehensions and generator iteration are the catchers (a comprehension internally *is* iteration); each level's handler either consumes the `Yield(v)` based on what it handles, or pops it up. This is precisely why the greenlet substrate and everything-yield-through-able exist. Consequences: a bare `gen= : yield 1` followed by `gen ()` is a loud unhandled-yield error — laziness requires the explicit `generator` wrapper; `for`/`while` need zero awareness of yield; `yield` remains fully shadowable; the compiler has no lexical yield knowledge at all.

Decisions:
- **Collectors are handlers.** `list`/`dict`/`set` catch `Yield` from their arguments behind the scenes and collect. Per-argument contract: a yielding argument contributes all its yielded values and its completion value is discarded; a non-yielding argument contributes its value itself (so `[1 2 3]` stays a literal and `[for (range 3) x: yield x*x]` is `[0, 1, 4]` without a duplicated tail). Edge cases (nested collection, wrong-shape yields for dict/set) belong to the runtime-library ticket.
- **`generator` wrapper contract.** `g= generator body`; calling `g ()` returns a lazy Gen that drives the body across sync points: `Yield(v)` → value to the consumer, `Resume(sent)` → continue, `Done(r)` → `StopIteration(r)`, native errors propagate; `close ()` injects GeneratorExit (discipline belongs to ticket 011). Wrapping a non-yielding lambda is legal: zero elements, immediate StopIteration.
- **v1 handler whitelist:** comprehension collectors and `generator` iteration only. No magic-method overriding (`__iter__`/`__next__`) in v1 — they complicate the story; Gen is a plain Python iterator purely for interop with Python consumers (numpy, list, for). User-defined handlers are ticket 012's territory and a pure increment later.
- **No `yield from` delegation in v1** (deferred to the runtime-library ticket); `yield` of a Gen yields the Gen itself.

**Amendment (owner review, 2025-09-01):** the `generator` wrapper is **deleted** — it was a redundant layer around what consumers already do. **A yielding lambda IS the generator**: any consumer that receives one (`list`, `dict`, `set`, `for`) drives it internally with its own handler active — `list gen` collects; `for gen x: body` iterates it. `list (gen ())` is a category error: arguments evaluate before the call, so the yield fires with no receiver. `gen ()` direct remains the loud unhandled-yield error. Consumers detect a lambda argument and switch to drive mode; non-lambda arguments keep the previous contract (Python iterables iterated, plain values collected). The v1 handler whitelist becomes: collectors and consumer iteration (`for`/`while` driving lambdas) — same mechanism, no wrapper.

**Amendment 2 (owner review):** collectors take **exactly one argument** — `list` cannot both drive a lambda and collect multiple values. Multi-value literals are brackets: `[a b]`. **Bracket duality** (same glue logic as infix): glued `a[i]` = subscript (`__getitem__`); space-separated/standalone `[a b]` = list literal, elements space-separated with the same inner grammar. `list gen` drives; `list (for …)` collects a yielding call-expression; `list 5` (neither lambda nor iterable) = TypeError. `dict`/`set` same single-argument contract; pairs are **tuples** (`yield k, v`).

Standing note: the asymmetry with `return` (ticket 001) holds — return bubbles the dynamic stack to the nearest **assigned** lambda frame (consumed lambdas are transparent), while yield is a dynamic effect bubbling to the nearest active **handler**; that asymmetry is exactly what makes `for … yield` comprehensions work inside consumed bodies.
