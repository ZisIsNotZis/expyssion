---
id: 014
title: "Python interop and the native-frame seam"
labels: [wayfinder:grilling]
status: closed
assignee: z
blocked-by: ["010"]
---

## Question

Specify both directions of interop: calling Python (stdlib, numpy) from expyssion — plain calls through sync points, C operations atomic; and Python calling into expyssion (callbacks, `sorted key=`, np.vectorize) — the seam where no `call()` wrapper runs, the "am I wrapped?" check, and the clean error for yield-across-native-frame. Also: iteration interop (our Gen consumed by Python consumers), pickling limits, and what the spec documents vs guarantees.

**Resolution (closed 2025-09-01, auto-run):** Python → expyssion: any Python callable is callable normally through sync points; C operations are atomic (switches never occur inside C code), so numpy-style workloads are safe. expyssion → Python: a lambda invoked bare from Python gets an auto entry-context (ticket 010); plain calls work, but a `yield` inside it has no handler and raises the loud unhandled-yield error — never silent corruption. Iteration is symmetric: `for` consumes any Python iterable; our Gen is consumed by any Python consumer (numpy, list, for). Attribute access, method calls, and operators on Python objects dispatch to Python's own machinery. import is a root builtin: `import name` binds the module object (alias by assignment). Not supported, documented: pickling lambdas (multiprocessing), forking with suspended chains, yields crossing native frames.

**Amendment (owner decision, 2025-09-01):** invoking a non-callable value (a number, list, string…) raises the native Python TypeError — the doc's "regular type ignores arguments and returns itself" rule is dropped.
