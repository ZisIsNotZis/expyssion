---
id: 003
title: "Assignment `=` and lvalues under the sync-point machine"
labels: [wayfinder:grilling]
status: closed
assignee: z
blocked-by: []
---

## Question

`=` has a "magical lvalue reference" argument and returns the RHS. Decide: statement compilation vs `call(_set, lvalue, v)`; whether "returns RHS" is universal or best-effort (name targets chain via walrus, item/attr targets statement-only?); how `a[0]= b` and `a.c= b` compile; whether `=` may appear in expression position and with what limits; how assignment inside lambda bodies interacts with the implicit-return-last-line rule.

**Resolution (closed 2025-09-01, auto-run):** `=` is hard-wired syntax (ticket 001). LHS forms: name, subscript `a[i]`, attribute `a.b`, and destructuring `(a b)= pair` (Python tuple assignment; nesting allowed). Compilation: in statement position, a direct Python assignment (thin skin); chained names `x= y= 3` compile to a walrus chain. Assignment evaluates to the RHS: in expression position, name-targets compile to walrus; item/attr-targets compile to a runtime `_set(target, v)` helper that returns v — the one documented exception to thin-skin output, with statement position as the preferred style. Inside lambda bodies: Python local semantics (assignment makes a local); if the last body line is an assignment, its RHS is the implicit return value. Augmented operators (`+= -= *= /= //=`) are sugar compiled to Python augmented assignment under the same position rules.

**Amendment (owner review, 2025-09-01):** augmented operators are **removed** (`count= count+ 1` instead) — not strictly necessary. Multi-character infix is **eliminated except where no single symbol exists**: `<= >= != ==` stay (and `**`); `//`, `&&`, `||` do not exist (floor division via a library function; logical and/or are prefix functions per ticket 004). **Tuples return via comma** (owner correction): `,` builds tuples — heterogeneous values go in tuples, homogeneous in lists; destructuring `(a b)= 3, 4`.
