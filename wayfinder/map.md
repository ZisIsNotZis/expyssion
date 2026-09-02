---
labels: [wayfinder:map]
---

# Wayfinder map: expyssion LANGUAGE.md v1 spec

## Destination

A finalized `LANGUAGE.md` v1: a precise, self-consistent specification of expyssion — the everything-is-a-call language whose execution model is the sync-point effect machine (S1⁺, see [ADR 0001](../docs/adr/0001-sync-point-effect-machine.md)) — with grammar, every construct's semantics, and the Python-transpilation story locked. Spec only; no implementation code.

## Notes

- Domain: programming-language design for a personal expression language that transpiles to Python. Consult the **grilling** and **domain-modeling** skills every session; glossary lives in [CONTEXT.md](../CONTEXT.md).
- Standing preferences settled while charting: syntax identity holds (prefix calls, `:` lambdas, no keywords); transpilation tier (b) — a Python-hosted runtime machine — accepted deliberately over thin-skin; `yield` across lambda boundaries is a must-have (comprehensions are yields); depth parameters are banned from surface syntax (return bubbles the dynamic stack to the nearest assigned lambda; break/continue dynamic); sync-point elision is a pure optimization; blocking world chosen (asyncio out); greenlet is the substrate with thread-per-generator as stdlib fallback.
- Decisions made during charting live in the ADR and CONTEXT.md, not in tickets; this map covers what remained open.
- Tracker is local markdown (`wayfinder/`); blocking is expressed by each ticket's `blocked-by` field; claim a ticket by setting `assignee` before working it.
- **2025-09-01: the map owner authorized an auto-resolution run** ("auto next until full done"). Tickets 003–008 and 010–016 were resolved autonomously in one session, applying the standing preferences above; each resolution records its rationale and may be reopened by the owner.

## Decisions so far

- [ADR 0001: sync-point effect machine](../docs/adr/0001-sync-point-effect-machine.md): S1⁺ adopted over pure-runtime-depth and special-forms designs; yield becomes a shadowable library effect; con ledger recorded.
- [Greenlet runtime facts: GC, cancellation, tracing, threads](tickets/009-greenlet-runtime-facts.md): closed — cyclic suspended chains leak (close discipline normative); recursion counter not reset by greenlet (ADR corrected); thread affinity errors cleanly; tracebacks chain cleanly but grow with chain depth; ~0.9 µs per spawn+switch.
- [Control-flow message set: exceptions native or on the Result channel?](tickets/001-control-flow-message-set.md): closed — two-tube vocabulary: upward carries only the private `Yield(v)` wrapper or a bare completion value (no Err, no Done wrapper); downward is spawn-args vs resume-value, no container. Return bubbles the dynamic stack to the nearest assigned (`=`-RHS-born) lambda frame; consumed lambdas and builtin impls pass through; no depth parameter anywhere. break/continue dynamic (only loop impls catch them). `=` and `:` are hard-wired, unshadowable; other control-flow names shadowable.
- [Generator call semantics: marking, wrapper, or dynamic?](tickets/002-generator-call-semantics.md): closed — no lexical marking, **no `generator` wrapper**: a yielding lambda IS the generator; consumers (list/dict/set/for) drive lambda arguments internally with their handler active (`list gen`); `gen ()` bare = loud error; no `__iter__/__next__` overriding in v1; no `yield from` yet.
- [Assignment `=` and lvalues under the sync-point machine](tickets/003-assignment-and-lvalues.md): closed — statement-first compilation; destructuring `(a b)= list 3 4`; expression-position name targets via walrus, item/attr via `_set` helper; **no augmented operators**; multi-char infix only where no single symbol exists (`<= >= != ==`, `**`).
- [Grammar: indentation ownership, spacing vs parens, precedence](tickets/004-grammar-and-precedence.md): closed — last-token-owns-indented-lines formalized; paren = arglist attaching to nearest head (`f (a) (b)` = f(a,b)); **no `,` or `;` for arguments** (`,` = tuple builder, lowest precedence); **infix = symbols glued to LHS, every operator glued to its left operand, fixed arity — never variadic heads** (`a+ f 3` = a+ f(3)); `[ ]` = subscript with same inner grammar and exactly one index (`a[b c]` = a[b(c)]), slices via `slice` constructor; `[a b]` spaced = list literal; param annotations `name(:type)?(=default)?`, `..`/`...`, trailing nameless `:type` = return type; call-site kwargs `name:=value`; `:` body = one expression per line / indented block; `:` binds loosest; Python literals and truthity.
- [Scoping, closures, and name resolution](tickets/005-scoping-and-closures.md): closed — Python nested-def scoping; **assignment edits the nearest lexical ancestor scope where the name is bound (auto closure cells), else defines locally; no shadowing of outer names; no `global`/`nonlocal`**; loop gotcha impossible (per-iteration argument); root bindings shadowable.
- [Concurrency stance: threads, processes, asyncio cutoff](tickets/006-concurrency-stance.md): closed — thread-affine chains (normative); no cross-thread generators; multiprocessing/fork hazards documented; asyncio out; thread-per-generator = documented non-normative fallback.
- [Spec acceptance criteria and document structure](tickets/007-spec-acceptance-and-structure.md): closed — done = grammar+semantics complete, proof corpus with 3 verified litmus programs, library table; LANGUAGE.md spec proper + docs/transpilation.md; version line in header, git as changelog.
- [Language name: expyssion vs expyssoin](tickets/008-language-name.md): closed — canonical name is **expyssion**; `expyssoin` stays a directory name only.
- [Sync-point protocol formalization](tickets/010-sync-point-protocol.md): closed — normative machine: fresh greenlet per invocation, Start/Yield/Resume/Done wire, per-frame handler consume-or-bubble, try/finally GreenletExit exception-safety, auto entry seam, as-if elision clause, recursion bound documented.
- [Close, cancellation, and resource discipline](tickets/011-close-and-cancellation.md): closed — `close g` normative (GeneratorExit injection, finally runs); abandonment = documented GC fallback; `with_resource` HOF; don't yield across resource scopes; cycles leak (close before dropping).
- [Handler tagging and effect identity](tickets/012-handler-tagging.md): closed — v1 untagged Yield, builtin whitelist; tag field reserved; future user handlers match on tag, builtins use a private tag.
- [Sync-point elision rules](tickets/013-elision-rules.md): closed — as-if clause; elidable = unshadowed non-handler pure builtins only; never lambdas/handlers/shadowed names; mangled `_e.` emission path; traceback thinning documented.
- [Python interop and the native-frame seam](tickets/014-python-interop-seam.md): closed — Python callables callable normally; bare-entered lambdas auto-context (yield = loud error); iteration symmetric; import = root builtin; **non-callable invocation = native TypeError** (doc's "returns itself" dropped); pickling/fork/native-frame limits documented.
- [Tracebacks and error message design](tickets/015-tracebacks-and-errors.md): closed — normative loud-error vocabulary; chained tracebacks (verbose for deep chains, documented); greenlet.settrace debug hook promised; no py-spy promise.
- [Runtime library inventory and collector edge cases](tickets/016-runtime-library-inventory.md): closed — v1 table: control structures (optional else → null; while cond is a re-invoked lambda; try body handler, no finally), collectors drive lambda args, lazy map/filter, sequence helpers, `import name`; **call-site kwargs `name:=value` (very high precedence, no parens)**; **floor division = `int a/b`** (no `//`, no helper); slices via `slice` constructor; tuples via comma; no delegation; `-1` negative literal, `neg` for expressions; no generics for now.

## Not yet specified

<!-- empty: the way is clear. All former fog graduated or was absorbed: literal/operator semantics → ticket 004; library inventory → ticket 016; shadowing/hygiene → ticket 013; versioning → ticket 007; the proof corpus is destination work produced during the spec write-up (acceptance criteria in ticket 007). -->

## Out of scope

- Implementing the transpiler or runtime — v1 is a spec; implementation is a follow-up effort once the destination is reached.
- Repository publication, README, and GitHub setup — approval-gated by workspace policy.
- asyncio/async support — the blocking world was chosen deliberately.
- User-defined macros, reader macros, or multi-shot continuations — greenlets are single-shot; effects are the extensibility story.
