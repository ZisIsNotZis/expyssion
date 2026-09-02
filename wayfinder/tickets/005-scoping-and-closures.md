---
id: 005
title: "Scoping, closures, and name resolution"
labels: [wayfinder:grilling]
status: closed
assignee: z
blocked-by: []
---

## Question

Define name resolution: Python lexical scoping via nested defs is the presumed compilation target — confirm; what assignment declares (local by default?); how closures capture (late binding of loop variables?); whether `global`/`nonlocal` equivalents exist or are rejected; how runtime (root) names like `if`, `yield`, `list` resolve and what shadowing them means at spec level (hygiene interacts with the elision ticket).

**Resolution (closed 2025-09-01, auto-run):** scoping is Python's via nested-def compilation: assignment makes a name local to its lambda; closures capture by reference (late binding). The for-body element is passed as a per-iteration argument, so Python's late-binding loop gotcha cannot arise for loops. v1 has **no `global`/`nonlocal`**: outer names are read-only inside inner lambdas; mutable state goes through containers or stored lambdas (documented consequence, revisit-worthy if it pinches). The root environment holds ordinary shadowable bindings (ticket 001: everything except `=` and `:`). A program file is a top-level lambda body (the module); `import name` binds the module object locally.

**Amendment (owner review, 2025-09-01 — supersedes the local-assignment clause above):** the assignment rule: `x= v` edits the nearest **lexical ancestor** scope where `x` is already bound; dynamic callers never qualify (g receiving f is a stack ancestor but not a code ancestor — ignored); if no lexical ancestor binds the name, it defines a new local in the assignment's own scope. Implemented as automatic closure cells (the compiler emits `nonlocal` exactly when an inner lambda assigns a name bound in a lexical ancestor). Consequences: accumulators inside if/for/while bodies work naturally (`total= 0 ; for xs x: total= total+ x` edits the outer total); **outer names cannot be shadowed by inner assignment** (documented); an assignment to a never-bound name inside a consumed lambda defines it locally there (unreadable outside) — accepted.
