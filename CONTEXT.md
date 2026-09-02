# CONTEXT.md — expyssion glossary

Glossary only. Design rationale lives in docs/adr/, the plan in wayfinder/map.md, the language itself in LANGUAGE.md.

- **expyssion** — the language: everything is an expression; everything is a call. (Canonical name per ticket 008; the working directory was named `expyssoin` during design and has since been renamed to match.)
- **call (prefix)** — the one syntactic form: `f a b` is `f(a, b)`; an argument followed by indented lines is owned by it.
- **lambda** — deferred callable, written `:` (`x: x+y`); multi-line bodies return the last executed line's value.
- **special form** — *not part of expyssion*: there are none. Control structures are ordinary functions.
- **sync point** — the effect boundary conceptually installed at every call; the unit of suspension and resumption.
- **sync-point channel** — the two-tube protocol crossing sync points: upward (child → parent) carries the private `Yield(v)` wrapper or a bare completion value, plus native exceptions; downward (parent → child) carries spawn arguments or a resume value, no container.
- **effect handler** — a frame that answers a Result instead of bubbling it upward; resolution is dynamic (nearest active handler).
- **yield** — a library-level effect performed via the Result channel; suspends the innermost active generator-style handler. No depth parameter.
- **collector** — `list`/`dict`/`set` acting as comprehension handlers: a lambda argument is driven internally (handler active) and its yields collected; non-lambda arguments are iterated or collected as values.
- **generator** — a yielding lambda itself; it carries no wrapper — any consumer that receives it (`list`, `for`, …) drives it across sync points.
- **elision** — compiler omission of provably pure sync points; a pure optimization, invisible to semantics.
- **native-frame seam** — the boundary where C/Python code calls into expyssion without a sync point (e.g. callbacks); yields cannot cross it.
- **stored lambda** — a lambda born as the right-hand side of `=`; its invocation frame catches ReturnException, so a `return` inside it (or bubbling into it) makes it return normally.
- **consumed lambda** — a lambda born directly as a call argument; return-transparent: ReturnException passes through its frame toward the nearest assigned lambda on the dynamic stack.
- **reserved syntax** — `=` and `:` are hard-wired (magical LHS and parsing) and cannot be shadowed; all other names — including control-flow builtins — are shadowable.
- **symbol infix** — infix operators are symbols glued to their LHS, and every operator must be glued to its left operand (`a& b| c` ✓; `a& b | c` ✗); no word-infix; no `,` or `;` for arguments; multi-char only where unavoidable (`<= >= != ==`, `**`). Infix binds tighter than the argument boundary (`int a/b` = int(a/b); `f x+ y` = f(x+ y)); `:=` (kwargs) even tighter (no parens). `not` is a plain function; `and`/`or` are prefix functions (eager; thunk the second argument for short-circuit). `[ ]` is subscript (slices via the `slice` constructor); `[a b]` spaced = list literal.
- **truthity** — the language's truthiness notion applied by `if`/`while` to condition values.
