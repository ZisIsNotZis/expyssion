---
id: 015
title: "Tracebacks and error message design"
labels: [wayfinder:grilling]
status: closed
assignee: z
blocked-by: ["010"]
---

## Question

Standard tracebacks/profilers break at greenlet switches (verified: greenlet docs; stacks would read "call() in call() in call()"). Design the debugging experience as a first-class feature: how errors crossing sync points present (real source locations, greenlet.settrace integration), what the runtime's error vocabulary is (seam errors, unhandled-yield, close-during-suspend), and what tooling story the spec promises (py-spy, greenlet.settrace) vs leaves to the implementation.

**Resolution (closed 2025-09-01, auto-run):** normative loud-error vocabulary (all Exception subclasses carrying expyssion-source context): "unhandled yield outside generator context", "return outside function", "break/continue outside loop", "yield across native frame", "close of non-generator", collector wrong-shape errors. Native exceptions cross switches with chained tracebacks — clean for shallow chains, verbose for deep ones (verified); the spec documents this rather than hiding it. Python-origin errors surface as-is (Python parity). Debug mode: the runtime installs `greenlet.settrace` to annotate switches — that hook is the promised tooling surface; no py-spy promise (support unverified against primary sources).
