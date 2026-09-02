---
id: 010
title: "Sync-point protocol formalization"
labels: [wayfinder:grilling]
status: closed
assignee: z
blocked-by: ["001", "002", "009"]
---

## Question

Specify the machine precisely: the `call()` protocol (spawn, START/RESUME, the Result loop), handler resolution rules, multi-level bubbling and resumption (traced and confirmed sound at charting time), exception-safety when KeyboardInterrupt lands between protocol steps (unwind must GreenletExit outstanding children), thread-affinity assumptions, and the "am I wrapped?" check for the native-frame seam. Deliverable: protocol prose precise enough to implement twice identically; possibly a small executable prototype to validate, if the group decides the spec needs one.

**Resolution (closed 2025-09-01, auto-run):** the machine, normatively operational: every lambda invocation runs in a fresh greenlet. `call(f, *args)`: spawn `child = greenlet(f)`, switch with the call arguments (**Start**). The call-site loop inspects what comes back: a private `Yield(v)` wrapper → the frame's handler decides (per ticket 002: generator/collector consume, or bubble via `parent.switch(v)`); on **Resume(sent)** continue the loop (sent is what `_yield` returns); a bare value is **Done** → unwrap and return it. Native exceptions propagate at switch sites (verified clean chained tracebacks). Control-flow exceptions are internal BaseException subclasses per ticket 001: Return caught by assigned frames, Break/Continue by loop implementations. **Exception-safety:** `call` wraps the switch in try/finally — any unwind (KeyboardInterrupt) throws GreenletExit into a still-alive child, preventing orphaned chains (per the greenlet research facts). **Entry seam:** a compiled lambda entering bare from Python installs a minimal context; plain calls work, effects without a handler raise the loud error. **Elision:** semantics are stated as-if every call syncs; elision (ticket 013) must preserve observable behavior. **Bounds:** CPython's recursion limit still applies (research fact) — the runtime raises the limit and the spec documents the bound; thread affinity inherited from greenlet. The spec presents this as a state machine plus normative pseudocode appendix.
