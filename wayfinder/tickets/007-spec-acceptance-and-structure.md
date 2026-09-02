---
id: 007
title: "Spec acceptance criteria and document structure"
labels: [wayfinder:grilling]
status: closed
assignee: z
blocked-by: []
---

## Question

Define what "LANGUAGE.md v1 is done" means verifiably: a checklist of constructs whose semantics must be specified, the proof-of-transpilability artifact (hand-transpiled Python per example?), and how the spec is organized given the workspace rule that Markdown files stay under 200 lines (single file vs `docs/` split; what stays in LANGUAGE.md vs docs/). Also decide the revision/changelog convention.

**Resolution (closed 2025-09-01, auto-run):** **Done means all of:** (1) grammar complete per ticket 004, no TBD constructs; (2) every construct's semantics specified including the sync-point machine per ticket 010; (3) proof corpus: every LANGUAGE.md example has its hand-transpiled Python in docs/transpilation.md; (4) three litmus programs hand-transpiled and their output verified against real Python execution: fibonacci (recursion/if), a generator pipeline consumed by a comprehension, and a guard-style early return; (5) the library table complete per ticket 016. **Structure:** LANGUAGE.md is the spec proper and the single source of truth for the language (kept under the 200-line workspace rule by leaning on links); docs/transpilation.md carries the per-construct Python mapping and corpus; docs/adr/ holds rationale; CONTEXT.md the glossary. **Versioning:** a `Version:` line in the LANGUAGE.md header; git history is the changelog until publication demands more. The corpus itself is destination work produced during the spec write-up (/to-spec), not a decision ticket.
