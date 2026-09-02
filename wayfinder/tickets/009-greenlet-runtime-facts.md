---
id: 009
title: "Greenlet runtime facts: GC, cancellation, tracing, threads"
labels: [wayfinder:research]
status: closed
assignee: z
blocked-by: []
---

## Question

Research (AFK, against primary sources) the greenlet facts the protocol and lifecycle tickets depend on: exact GreenletExit/last-reference semantics and what finally blocks may rely on; the documented cycle-collection limitation and what reference patterns leak; thread-affinity rules and the thread-per-generator fallback pattern; tracing/profiling facilities (greenlet.settrace events, py-spy support); C-stack behavior per greenlet (recursion-depth implications, stack-slice cost); switch/spawn performance numbers; exception propagation across switches and traceback shape; free-threading status. Capture findings as a durable Markdown file linked from this ticket. Findings so far (to verify and extend) are in [ADR 0001](../../docs/adr/0001-sync-point-effect-machine.md).

**Resolution (closed 2025-09-01):** resolved by the driving session (user override after subagent connection failures; first-pass doc notes pre-dated it). Findings recorded durably in [research/greenlet-runtime-facts.md](../research/greenlet-runtime-facts.md), with empirical tests on greenlet 3.2.5 / CPython 3.9.25. Decision-relevant outcomes: (1) cyclic reference chains through suspended greenlet frames **leak** — close discipline must be normative (feeds ticket 011); (2) greenlet does **not** reset CPython's recursion counter — chain depth stays bounded by the recursion limit, ADR 0001 corrected (feeds ticket 010); (3) thread affinity is enforced with a clean `greenlet.error`, making the thread-per-generator fallback viable (feeds ticket 006); (4) exceptions crossing switches carry clean chained tracebacks — the debugging cost is traceback *length*, not corruption (feeds ticket 015); (5) spawn+switch ≈ 0.9 µs, two-way switch ≈ 0.7 µs, confirming the elision ticket's importance (013); (6) py-spy greenlet support could not be verified from primary sources — do not rely on it.
