---
id: 011
title: "Close, cancellation, and resource discipline"
labels: [wayfinder:grilling]
status: closed
assignee: z
blocked-by: ["010"]
---

## Question

Define the lifecycle rules the GC research makes mandatory: explicit close for generators (protocol, what GreenletExit does to suspended chains), the `with`-equivalent HOF and its behavior when the body abandons via yield, what the spec promises about finally-timing, and the documented leak patterns (reference-dense chains, cycles through greenlet frame data). Decide what is normative discipline vs documented hazard.

**Resolution (closed 2025-09-01, auto-run):** normative: generators expose `close g`, injecting GeneratorExit into the live chain so every finally along it runs (compatible with Python's `contextlib.closing`). Abandonment without close is a documented fallback: GC eventually throws GreenletExit, nondeterministically — never the recommended path. `with_resource acquire (:r: body)` is the with-equivalent HOF (finally-based cleanup); yielding across a resource scope defers cleanup to GC — normative guidance: don't yield across resource scopes, or close deterministically. Cycles through suspended frames may leak (verified against greenlet's documented GC limitation) — normative: close before dropping; the runtime does not collect chain cycles. Cancelling a deep chain: the GeneratorExit propagates and intermediate finallys run on the way out.

**Amendment (owner review, after ticket 002's wrapper deletion):** with no `generator` wrapper, cleanup is **driver-owned**: the consumer's driving loop (for/while/list) try/finally-wraps the drive, and on break, error, or abandonment it injects GeneratorExit into the suspended chain — so `for g line: break` still closes the with_resource inside g deterministically. Abandonment without any driver (a yielding lambda never consumed) has nothing to clean up — no chain ever started.
