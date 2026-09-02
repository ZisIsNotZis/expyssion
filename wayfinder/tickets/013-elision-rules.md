---
id: 013
title: "Sync-point elision rules"
labels: [wayfinder:grilling]
status: closed
assignee: z
blocked-by: ["010"]
---

## Question

Define exactly when the compiler may omit a sync point without changing observable semantics: unshadowed builtin operators and known-pure runtime functions; what binding-resolution proof is required; how shadowing reintroduces sync points; interaction with lexical marking (ticket 002); and the "as-if" clause wording that makes elision a pure optimization in the spec rather than a semantics fork.

**Resolution (closed 2025-09-01, auto-run):** the spec's as-if clause: semantics are defined with every call a sync point; elision is a pure optimization that must preserve observable behavior. Elidable in v1, conservatively: a call whose head resolves — by lexical binding resolution with no shadowing in any enclosing scope — to a non-handler pure builtin (arithmetic, comparisons, subscript reads, truthity tests). Never elidable: any lambda invocation, any handler (`list/dict/set/generator`), any shadowed name; `=` and `:` are syntax and never synced. Shadowing a builtin simply disables its elision — equivalence guaranteed by the as-if clause. Hygiene: compiler emissions reference the runtime through a mangled module path (`_e.`) so user shadowing can never capture machinery. Documented observable difference: tracebacks may show fewer sync frames under elision.
