# expyssion — expression py

Version: 1.0 · everything is an expression; everything is a call

Glossary: [CONTEXT.md](CONTEXT.md) · Proof corpus: [docs/transpilation.md](docs/transpilation.md) · Rationale: [docs/adr/0001-sync-point-effect-machine.md](docs/adr/0001-sync-point-effect-machine.md) · Substrate facts: [wayfinder/research/greenlet-runtime-facts.md](wayfinder/research/greenlet-runtime-facts.md)

expyssion is a personal expression language that transpiles to Python. There are no keywords: control structures are ordinary functions of callables, and the only hard-wired syntax is `=` and `:` — every other name, including builtin control structures, can be shadowed. Semantics are defined by the sync-point effect machine (§8): every call behaves as-if it runs at a sync point on greenlets, which is what lets `yield`, `return`, and `break` cross lambda boundaries. Literals and truthity are Python's, including f-strings.

## 1 Calls and blocks

- `a b c` is `a(b, c)`: a head followed by space-separated sibling arguments.
- The last token of a line owns the following deeper-indented lines; sibling lines at the same depth are sibling arguments of that owner. `a b` with indented `c` is `a(b(c))`; `a` with indented `b`, `c` is `a(b, c)`.
- A paren group after a head is that head's arglist and attaches to the nearest head: `f (a) (b)` is `f(a, b)`. Inside an arglist the content is one expression: `f (a b c)` is `f(a(b, c))`.
- Group with parens to call a returned function: `(make_adder 3) 5`.
- A same-line lambda body is one expression: `: a b c` is `lambda: a(b, c)`. Multi-statement bodies are indented blocks; a block's value is its last expression (implicit return).
- `#` starts a comment. One expression per line — there is no `;`.

## 2 Infix

- Infix operators are symbols glued to their left operand, and every operator must be glued to its left operand. `a& b| c` is `(a&b)|c`; `a& b | c` and `a and b` are syntax errors.
- Operators have fixed arity (most: one LHS, one RHS) and are never variadic heads: `x+ f 3` is `x + f(3)`; `(x+ f) 3` calls the sum.
- Precedence follows Python's table (`* / %` above `+ -` above `<< >> & ^ |` above comparisons); comparisons chain Python-style. Override with parens: `(a& b)| c`.
- An argument or operand is a maximal infix expression: `int a/b` is `int(a/b)`; `f x+ y` is `f(x+ y)` — separate arguments need `f x y`.
- Multi-character operators exist only where no single symbol can: `== != <= >= << >> **`. There is no `//`, `&&`, `||` — floor division is `int a/b`, logic is below.
- `and`/`or` are prefix functions (`and a b`), evaluated eagerly; short-circuit with a thunk: `and a (: b)`. `not` is a plain function.
- Unary: `-1` is a folded negative literal; expression negation is `0- x` or `neg x` — a detached `-` is never an operator.

## 3 Postfix and brackets

- `a.b` is attribute access and binds tightest; `a.b c` is the method call `a.b(c)`. `a .b` is invalid.
- Glued `[ ]` is subscript with exactly one index expression: `xs[1]`; `a[b c]` is `a[b(c)]`; multiple indices need a tuple: `a[b, c]`.
- A space-separated `[ … ]` is a list literal; its elements are space-separated expressions: `[a b]` is `[a, b]`; `f [a b]` passes one list.
- Slices use the constructor: `xs[slice 1 3]`.
- `,` builds a tuple (lowest precedence) — the heterogeneous container; lists are the homogeneous container: `3, 4`; `yield k, v`; destructuring `(a b)= 3, 4`.
- Invoking a non-callable value raises the native Python TypeError.

## 4 Lambdas, parameters, kwargs

- `params: body`; params are space-separated in an optional paren group; bare `:` is zero params.
- Param-list context (a paren group followed by `:`): `name(:type)?(=default)?`, vararg `..(:type)?`, kwarg `...(:type)?`, and a trailing nameless `:type` declares the return type — `add= (a:int b:int :int): a+ b`. `..`/`...` are ordinary special variable names in the body. Annotations are documentation-only in v1; no generics.
- Call-site kwargs use `name:=value` — very high precedence, no parens: `connect "example.com" port:= 8080`. Extras land in `...`; kwargs come after positionals.
- `=` is hard-wired and cannot be shadowed; see §1 for what can.

## 5 Assignment and scoping

- Targets: name, subscript `a[i]`, attribute `a.c`, destructuring `(a b)= 3, 4`. No augmented operators: write `count= count+ 1`.
- Assignment evaluates to its RHS. In expression position a name target compiles to walrus; item/attr targets compile to a runtime set-helper (the one documented thin-skin exception). Chaining: `x= y= 3`.
- `x= v` edits the nearest lexical ancestor scope where `x` is bound (automatic closure cells); if none, it defines a local in the assignment's own scope. Dynamic callers never qualify — g receiving f is a stack ancestor but not a code ancestor. Consequences: accumulators work inside if/for/while bodies; outer names cannot be shadowed by inner assignment; there is no `global`/`nonlocal`.

## 6 Control flow

All control structures are ordinary functions of callables; loud errors (§12) make misplaced control flow visible.

- `if c t (e?)` — branches are **invoked callables**; literal branches must be wrapped as thunks: `odd_even= if x%2 (:"odd") :"even"`. A missing else yields null.
- Higher-order builtin arguments are invoked — pass thunks `(:v)` for literal values. Value-taking logic operators (`and`/`or`/`not`) are the exception: they receive plain values.
- `while cond body (else?)` — `cond` is a lambda re-invoked per iteration: `while (: x> 0) : …`.
- `for iter body (else?)` — `body` takes the element (or ignores it); `iter` may be any Python iterable **or a yielding lambda**, which the loop drives (§7). `else` runs on completion without break; for/while return the last body value.
- `try body handler` — `handler` receives the exception; re-raise with `raise`. No finally: use `with_resource` (§11). `raise exc` requires an exception instance.
- `return v` bubbles the dynamic stack to the nearest **assigned** lambda frame (born from `=`); **consumed** lambdas (born as call arguments) are transparent — `clip= x: if x<0 :return 0 ; x` returns 0. A return with no assigned frame above is a loud error. A callback's return returns from its callee at the invocation point.
- `break`/`continue` propagate to the nearest active loop implementation; everything else ignores them. No loop → loud error.

## 7 Yield, generators, comprehensions

- `yield v` propagates like a resumable exception to the nearest active handler; there is no wrapper, no marking, and no generator type — **a yielding lambda is the generator**, and whoever consumes it drives it with its handler active.
- Consumers drive lambda arguments: `list gen`, `for gen x: …`, `dict gen`. A yielding call-expression argument is collected as it evaluates: `list (for (range 3) x: yield x*x)` is `[0, 1, 4]`. `gen ()` bare → loud unhandled-yield error.
- Collectors: `list`/`dict`/`set` take exactly one argument; `dict` consumes key/value tuples: `dict (for (zip ks vs) (k v): yield k, v)`. Nested collectors: the nearest active handler wins.
- No `yield from` in v1 (yielding a lambda yields the lambda); no `__iter__`/`__next__` overriding; driven iterators interoperate with Python consumers.

## 8 Execution model

- Normative machine (ADR 0001): every lambda invocation runs in a fresh greenlet. Upward: the private `Yield(v)` wrapper or a bare completion value, plus native exceptions; downward: start-args or resume-values. Each frame's handler consumes or bubbles. `return`/`break`/`continue` are internal BaseException subclasses. Unwinds are exception-safe: GreenExit is injected into live children.
- Bare entry from Python installs an auto context: plain calls work; effects without a handler raise loud errors; yields cannot cross native frames.
- Elision is a pure optimization under the as-if clause: only unshadowed non-handler pure builtins compile without sync points; runtime emissions use a mangled `_e.` path; tracebacks may thin. CPython's recursion limit still bounds chain depth — the runtime raises it; see the substrate facts.

## 9 Standard library

- Control: `if c t (e?)`, `while cond body (else?)`, `for iter body (else?)`, `try body handler`, `raise exc`, `with_resource acquire (:r: body)`.
- Collectors: `list x`, `dict x`, `set x` (exactly one argument).
- Sequences & values: `range zip len map filter first sorted enumerate reversed sum min max abs print str int float isinstance getattr neg` — lazy `map`/`filter`; floor division is `int a/b`.
- Modules: `import name` binds the module object; reach everything else by attribute.

## 10 Python interop

- Any Python callable is callable normally; C operations are atomic (switches never occur inside C code).
- Lambdas called bare from Python run with an auto context: plain calls work; `yield` raises the loud unhandled-yield error.
- Iteration is symmetric: `for` consumes any Python iterable; driven generators are plain Python iterators.
- Not supported, documented: pickling lambdas, forking with suspended chains, yields crossing native frames.

## 11 Concurrency and lifecycle

- Greenlet chains are thread-affine; a suspended chain resumes only on its creating thread; cross-thread switch raises a clean error.
- Cleanup is driver-owned: on break, error, or abandonment the driving loop injects GeneratorExit into the suspended chain, running every finally on the way out. Abandonment without a driver starts no chain; the GC fallback is nondeterministic and documented. Cycles through suspended frames may leak — close before dropping.
- `with_resource acquire (:r: body)` is the with-equivalent; do not yield across resource scopes without closing.
- Signal handlers must not switch greenlets. asyncio is out of scope — expyssion is a blocking language.

## 12 Errors

- Normative loud errors: "unhandled yield outside generator context", "return outside function", "break/continue outside loop", "yield across native frame", "close of non-generator", collector wrong-shape.
- All runtime errors are Exception subclasses carrying expyssion-source context; Python-origin errors surface as-is; tracebacks chain across switches and grow with chain depth (documented).
- Debug mode installs `greenlet.settrace` to annotate switches. No py-spy promise.
