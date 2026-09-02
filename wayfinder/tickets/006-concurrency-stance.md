---
id: 006
title: "Concurrency stance: threads, processes, asyncio cutoff"
labels: [wayfinder:grilling]
status: closed
assignee: z
blocked-by: []
---

## Question

Write the concurrency contract on the tin: greenlet chains are thread-affine (a suspended chain resumes only on its owning thread); multiprocessing is unsupported for lambdas (pickling) and forking with suspended chains is hazardous; asyncio interop is out (blocking world). Decide what, if anything, the spec promises for thread-based parallelism (numpy's GIL release is the numeric story), whether a documented thread-per-generator fallback is normative or a footnote, and what the spec says about signal handlers (must not switch).

**Resolution (closed 2025-09-01, auto-run):** normative contract: greenlet chains are thread-affine — a suspended chain resumes only on its creating thread; cross-thread switch is a clean error (verified). Generators must be consumed on their creating thread. Independent expyssion programs may run on different Python threads; sharing suspended chains across threads is unsupported. Numeric parallelism = numpy's GIL release driven from a single expyssion thread. multiprocessing: unsupported for lambdas (unpicklable) and fork-with-suspended-chains is a documented hazard. asyncio: out — the blocking world was chosen. Signal handlers must not switch greenlets (greenlet caveat, normative). The thread-per-generator substrate with the same wire protocol is documented as the stdlib fallback, non-normative.
