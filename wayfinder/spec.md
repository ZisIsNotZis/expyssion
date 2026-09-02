---
labels: [ready-for-agent, spec]
id: spec-language-v1
---

## Problem Statement

The language designer of expyssion has settled every design decision through a wayfinder effort (16 closed decision tickets, one ADR, verified greenlet research), but the artifacts are scattered: `LANGUAGE.md` is a stale early sketch with known bugs and superseded semantics, and the real decisions live in tickets and a decision-examples file. There is no single authoritative, self-consistent specification — so the language cannot be referenced, taught, reviewed, or implemented.

## Solution

Write **LANGUAGE.md v1** — the finalized, self-consistent specification of expyssion (canonical name, ticket 008) — plus its companion `docs/transpilation.md` proof corpus. The spec document is the deliverable: precise grammar, per-construct semantics (defined as the sync-point effect machine, ADR 0001), the v1 standard-library table, and a hand-transpilation proof for every example. No implementation code.

## User Stories

1. As the language designer, I want a single self-consistent LANGUAGE.md v1, so that every future discussion, review, and implementation references one source of truth.
2. As a programmer, I want everything to be an expression, so that any fragment composes into larger programs.
3. As a programmer, I want prefix calls with space-separated sibling arguments (`a b c` = a(b, c)), so that calls read cleanly without punctuation.
4. As a programmer, I want the last token of a line to own following indented lines, so that blocks nest without explicit delimiters (with the documented quirk that `a b` + indented `c` is a(b(c))).
5. As a programmer, I want paren arglists to attach to the nearest head (`f (a) (b)` = f(a, b)), so that grouping is predictable.
6. As a programmer, I want infix operators to be symbols glued to their left operand (`a& b| c`), so that word-infix ambiguity cannot exist.
7. As a programmer, I want every infix operator to have fixed arity and never act as a variadic head, so that `x+ f 3` is always x + f(3) and `(x+ f) 3` calls the sum.
8. As a programmer, I want a symbol precedence table (arithmetic above adjacency boundaries), so that `int a/b` means int(a/b) without parens.
9. As a programmer, I want glued `[ ]` to be subscript with exactly one index (`a[b c]` = a[b(c)]), so that indexing is unambiguous.
10. As a programmer, I want space-separated `[a b]` to be a list literal, so that homogeneous collections are cheap to write.
11. As a programmer, I want `,` to build tuples (heterogeneous container) with lowest precedence, so that `yield k, v` and destructuring `(a b)= 3, 4` read naturally.
12. As a programmer, I want slices via the slice constructor (`xs[slice 1 3]`), so that the grammar needs no slice syntax.
13. As a programmer, I want lambdas written `params: body` with the body being one expression per line or an indented block returning its last value, so that deferred behavior needs no keywords.
14. As a programmer, I want parameter annotations `name(:type)?(=default)?`, vararg `..`, kwarg `...`, and a trailing nameless `:type` return annotation, so that signatures are documentable without runtime enforcement.
15. As a programmer, I want call-site kwargs via `name:=value` (very high precedence, no parens), so that keyword passing never collides with assignment, booleans, or lambda arguments.
16. As a programmer, I want negative number literals (`-1`) with expression negation via `0- x` or `neg`, so that the glue rule never meets a detached minus.
17. As a programmer, I want assignment (`=`, hard-wired with `:`) to target the nearest lexical ancestor scope where the name is bound and define locally otherwise, so that accumulators work inside if/for/while bodies without scope keywords.
18. As a programmer, I want dynamic callers to never receive my assignments, so that passing my lambda to someone cannot let them mutate my scope.
19. As a programmer, I want destructuring (`(a b)= 3, 4`), chained walrus (`x= y= 3`), and attribute/subscript assignment, so that assignment covers the everyday cases.
20. As a programmer, I want control structures as ordinary functions of callables (`if c t (e?)`, `while cond body (else?)`, `for iter body (else?)`, `try body handler`), so that the language has no control-flow keywords.
21. As a programmer, I want `while`'s condition to be a re-invoked lambda, so that conditions are re-evaluated each iteration under call-by-value.
22. As a programmer, I want `return` to bubble the dynamic stack to the nearest assigned (born-from-`=`) lambda frame, so that guard clauses cross consumed structure bodies but user callbacks never leak returns.
23. As a programmer, I want `break`/`continue` to be caught only by loop implementations, so that loops are the sole interpreters of loop control.
24. As a programmer, I want loud errors for unhandled `return`/`break`/`continue`/`yield`, so that misplaced control flow is never silently swallowed.
25. As a programmer, I want `yield` to propagate like a resumable exception to the nearest active handler, so that yielding works through any depth of consumed lambdas.
26. As a programmer, I want comprehension collectors (`list`/`dict`/`set`) and consumer iteration to drive yielding lambdas internally, so that comprehensions are pure library with no wrapper, no marking, and no magic methods.
27. As a programmer, I want a bare call of a yielding lambda to raise a loud unhandled-yield error, so that effects are never dropped.
28. As a reviewer, I want the semantics defined as-if every call is a sync point on greenlets (normative machine: Start/Yield/Resume/Done, per-frame consume-or-bubble, exception-safe unwinds), so that the language's meaning is implementation-independent.
29. As a reviewer, I want elision stated as a pure optimization (only unshadowed non-handler pure builtins; mangled `_e.` emission path), so that optimized output remains spec-equivalent.
30. As a Python interop user, I want any Python callable callable from expyssion and our lambdas consumable as plain Python callables/iterators, so that the Python ecosystem stays reachable.
31. As a Python interop user, I want non-callable invocation to raise the native TypeError, so that errors match Python's own.
32. As a debugger, I want a normative loud-error vocabulary and the `greenlet.settrace` debug hook documented, so that misbehaving programs are diagnosable.
33. As a maintainer, I want the concurrency contract written (thread-affine chains, no cross-thread generators, fork/pickling hazards, asyncio out), so that misuse is a documented boundary, not a surprise.
34. As a maintainer, I want driver-owned cleanup (consumers inject GeneratorExit on break/error) and the close/abandon discipline documented, so that resources close deterministically where possible.
35. As the language designer, I want the spec split per the workspace rules (LANGUAGE.md lean and under 200 lines, corpus in docs/transpilation.md, rationale in docs/adr/, glossary in CONTEXT.md) with a version header, so that the document set stays navigable.

## Implementation Decisions

- **Execution model (ADR 0001, tickets 010/001):** the sync-point effect machine is normative — every lambda invocation runs in a fresh greenlet; upward carries the private `Yield(v)` wrapper or a bare completion value plus native exceptions; downward carries start-args or resume-values; per-frame handlers consume or bubble; `call` unwinds exception-safely via GreenletExit injection; bare Python entry installs an auto context. Spec states semantics as-if every call syncs.
- **Control flow (001):** `return`/`break`/`continue` are internal BaseException subclasses; assigned frames catch Return, loop implementations catch Break/Continue; no depth parameters anywhere; `=` and `:` are hard-wired unshadowable syntax, all other names shadowable; rejected alternatives recorded (Err-on-channel, all-messages-on-channel, storer-abort).
- **Grammar (004 + amendments):** indentation ownership; paren arglists attach to nearest head; symbol infix glued to LHS with fixed arity; `,` = tuple builder; `[ ]` bracket duality (glued subscript with single index, spaced list literal); slices via `slice` constructor; `:` body = one expression per line / indented block; param annotations, `..`/`...`, trailing return type; call-site kwargs `name:=value` (very high precedence); negative literals; Python literals and truthity; `import name` syntax.
- **Assignment & scoping (003/005):** assignment targets nearest lexical ancestor binding (auto closure cells), else local; no shadowing of outer names; no `global`/`nonlocal`; destructuring and walrus per ticket 003; no augmented operators.
- **Generators & comprehensions (002):** no wrapper, no marking — yielding lambdas are driven by their consumers; collectors take exactly one argument; pairs are tuples; no `yield from`, no `__iter__`/`__next__` overriding in v1.
- **Library (016):** control-structure signatures (optional else → null; `try body handler`, no finally), lazy `map`/`filter`, sequence helpers, curated re-exports; floor division = `int a/b`; no generics, no augmented operators.
- **Elision (013):** as-if clause; elidable = unshadowed non-handler pure builtins only; mangled `_e.` emission path; traceback thinning documented.
- **Interop & errors (014/015):** C-atomic calls, auto entry seam, native TypeError for non-callables, normative loud-error vocabulary, `greenlet.settrace` debug hook, no py-spy promise.
- **Concurrency (006) & lifecycle (011):** thread-affine chains; driver-owned cleanup with GeneratorExit injection; GC fallback and cycle-leak hazards documented.
- **Docs (007/008):** canonical name expyssion; LANGUAGE.md (spec proper, <200 lines, `Version:` header) + docs/transpilation.md (corpus) + docs/adr/ + CONTEXT.md; git history as changelog.

## Testing Decisions

- **The seam is the corpus itself** (highest possible for a document deliverable): every example in LANGUAGE.md must appear in docs/transpilation.md with hand-transpiled Python that *actually executes* and produces the example's claimed output.
- Three litmus programs get end-to-end verification against real Python execution: fibonacci (recursion/if), a generator pipeline consumed by a comprehension, and a guard-style early return.
- Every grammar rule in LANGUAGE.md must be exercised by at least one corpus example (rule-coverage check).
- Good tests here are behavioral only: claimed outputs vs real Python execution — never implementation details, since no implementation exists.
- Prior art: none (greenfield); `wayfinder/research/decision-examples.md` (rev 3) is the seed corpus and `wayfinder/research/greenlet-runtime-facts.md` the verified substrate facts.

## Out of Scope

- Implementing the transpiler or runtime (follow-up effort once this spec lands).
- Repository publication, README, GitHub setup (approval-gated).
- asyncio/async support; user-defined effect handlers and tags (extension contract reserved); macros; multi-shot continuations; generics; runtime type enforcement; `yield from` delegation; augmented operators; magic-method overrides.

## Further Notes

- Provenance: all decisions come from the closed wayfinder tickets (wayfinder/map.md, 16/16 resolved — 003–008 and 010–016 were resolved in one owner-authorized auto-run and are reopenable); rationale in docs/adr/0001; substrate facts in wayfinder/research/greenlet-runtime-facts.md; the seed corpus is wayfinder/research/decision-examples.md (rev 3).
- The owner flagged tickets 010, 004, and 016 as most deserving of a personal review pass before the spec hardens.
- Known documented sharp edges to carry into LANGUAGE.md: a callback's return aborts its callee's remaining body; cycles through suspended frames leak; deep chains produce verbose tracebacks; an assignment to a never-bound name inside a consumed lambda is local to it.
