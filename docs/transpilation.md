# expyssion — transpilation proof corpus

Proof artifact for LANGUAGE.md v1 (spec: wayfinder/spec.md, ticket 007). Every construct maps to plain, readable Python — the "elided" form below is what a compliant compiler may emit; the "as-if" form is the normative semantics when it must not inline (ticket 013).

**Verification:** `docs/verify_corpus.py` — 40 checks, all passing (2025-09-01, CPython 3.9 + greenlet 3.2.5 + numpy 2.0). Markers: ▶ executed & verified · ◇ normative-only (needs the runtime; spec-defined, not executable here).

## Calls & blocks

| expyssion | elided Python |
|---|---|
| `a b c` | `a(b, c)` ▶ |
| `a b` + indented `c` | `a(b(c))` ▶ |
| `f (a b c)` | `f(a(b, c))` ▶ |
| `f (a) (b)` | `f(a, b)` ▶ |
| `(make_adder 3) 5` | `make_adder(3)(5)` ▶ |
| `: a b c` | `lambda: a(b, c)` ▶ |

Multi-statement lambda bodies are indented blocks with implicit return of the last value ▶ (see `g`/`sum_all` below).

## Infix

| expyssion | elided Python | verified output |
|---|---|---|
| `1+ 2*3` | `1 + 2 * 3` | `7` ▶ |
| `a& b| c` | `(a & b) \| c` | `3` (a=1,b=3,c=2) ▶ |
| `x+ f 3` | `x + f(3)` | `31` (x=1) ▶ |
| `int a/b` | `int(a / b)` | `3` (7/2) ▶ |
| `a& b | c` | syntax error — an operator with nothing glued before it | ◇ |
| `a and b` | syntax error — no word-infix | ◇ |

`and`/`or` are prefix functions, evaluated eagerly ▶ (`_and(True, 5) == 5`, `_and(False, 5) is False`). Short-circuit is the thunk idiom `and a (: b)` → `def _and(a, b_fn): return b_fn() if a else a` — verified the thunk is skipped when falsy ▶. `not` is a plain function ▶. `-1` is a folded negative literal; expression negation is `neg x` or `0- x` ▶.

## Postfix & brackets

| expyssion | elided Python | verified |
|---|---|---|
| `a.b c` | `a.b(c)` | ▶ |
| `xs[1]` | `xs[1]` | ▶ |
| `a[b c]` | `a[b(c)]` — subscript takes exactly one index | ▶ |
| `xs[slice 1 3]` | `xs[slice(1, 3)]` | ▶ |
| `[a b]` | `[a, b]` — spaced bracket = list literal | ▶ |
| `f [a b]` | `f([a, b])` — the list is one argument | ▶ |
| `xs [i]` | `xs([i])` — a call, not a subscript | ◇ |
| `xs 5` | native `TypeError` | ▶ |

## Tuples & lists

| expyssion | elided Python |
|---|---|
| `3, 4` | `(3, 4)` ▶ |
| `(a b)= 3, 4` | `a, b = 3, 4` ▶ |
| `x= y= 3` | `x = y = 3` ▶ |
| `k, v` (yielded to dict) | tuple pair ▶ |

## Lambdas, annotations, kwargs

| expyssion | elided Python |
|---|---|
| `add= (x y): x+ y` | `def add(x, y): return x + y` ▶ |
| `add= (a:int b:int :int): a+ b` | `def add(a: int, b: int) -> int: …` ▶ |
| `connect= (host:string port:int= 80): …` | `def connect(host: str, port: int = 80): …` ▶ |
| `connect "example.com"` | `connect("example.com")` → `("example.com", 80)` ▶ |
| `connect "example.com" port:= 8080` | `connect("example.com", port=8080)` ▶ |
| `sum_all= (..:int): …` | `def sum_all(*args: int): …` ▶ (`sum_all(1,2,3) = 6`) |
| `f= (...:dict): …` | `def f(**kwargs: dict): …` ◇ |

Annotations are documentation-only in v1 (no runtime enforcement). No generics.

## Assignment & scoping

| expyssion | elided Python |
|---|---|
| `x= 3` / `a[0]= b` / `a.c= b` | `x = 3` / `a[0] = b` / `a.c = b` ▶ |
| `x= y= 3` | `x = y = 3` ▶ |
| `(a b)= 3, 4` | `a, b = 3, 4` ▶ |
| `count= count+ 1` | `count = count + 1` (no augmented operators) ▶ |

Assignment edits the nearest lexical ancestor binding (auto closure cells), else defines locally — `make_counter` returns a closure whose `n= n+ 1` compiles to `nonlocal n` ▶ (verified 1, 2); accumulators inside for bodies edit the enclosing total ▶ (verified 6). Dynamic callers never qualify (g receiving f is not a code ancestor); outer names cannot be shadowed by inner assignment ◇.

## Control flow

| expyssion | elided Python |
|---|---|
| `if c t e` | `t() if c else e()` — branches are invoked callables; literals wrapped as thunks `(:v)` ▶ |
| `if c t` (no else) | `t if c else None` ▶ |
| `clip= x: if x<0 :return 0 ; x` | see below ▶ |
| `while (: x> 0) : …` | `while x > 0: …` ▶ |
| `for iter body (else?)` | `for x in iter: …` (else runs without break) ▶ |
| `try body handler` | `try: body() except Exception as e: handler(e)` ▶ |

clip, elided (the consumed if-body is transparent to return):

```python
def clip(x):
    if x < 0:
        return 0
    return x
```

clip, as-if (normative machine form — the then-branch raises Return, caught by the assigned frame):

```python
def clip(x):
    try:
        _e.if_(x < 0, lambda: _e.raise_return(0), lambda: _e.null)
        return x
    except _e.Return as r:
        return r.value
```

◇ Normative-only (machine semantics; needs the runtime): Return caught by assigned frames; Break/Continue caught only by loop implementations; loud errors ("return outside function", "break/continue outside loop", "unhandled yield outside generator context", "yield across native frame"); GeneratorExit injection on driver unwind; thread-affinity errors ▶ (verified separately: cross-thread switch raises `error` — see verify_corpus.py).

## Yield, generators, comprehensions

A yielding lambda *is* the generator — consumers drive it:

| expyssion | elided Python | verified |
|---|---|---|
| `gen= : yield 1` + `list gen` | `def gen(): yield 1` → `list(gen())` = `[1]` | ▶ |
| `list (for (range 3) x: yield x*x)` | `[x*x for x in range(3)]` = `[0, 1, 4]` | ▶ |
| `dict (for (zip ks vs) (k v): yield k, v)` | `{k: v for k, v in zip(ks, vs)}` | ▶ |
| `for gen x: print x` | `for x in gen(): print(x)` | ▶ |
| `list (for nums x: if x%3==0 :yield x*x)` | `[x*x for x in nums() if x%3==0]` | ▶ |
| nested collectors (nearest handler wins) | `[[y for y in range(2)] for _ in range(3)]` = `[[0,1],[0,1],[0,1]]` | ▶ |
| `gen ()` bare | loud unhandled-yield error | ◇ |

Machine walk (as-if): `list`'s call loop spawns the for-call; each body `yield` bubbles `Yield(v)` to list's handler → collect, `Resume`; body `Done` → list returns the collected list ◇.

## Library highlights

`int a/b` floor division ▶ · `neg x` ▶ · `map`/`filter` lazy ▶ · `first` via `next` ▶ · `range zip len sorted print isinstance getattr str int float sum min max abs enumerate reversed` re-exported ◇ · `import name` binds the module object ▶ (`np.arange 10`, `a.max ()` with numpy ▶) · `with_resource acquire (:r: body)` — finally-based cleanup; drivers inject GeneratorExit on break/error ◇ · no `//`, no augmented operators, no `yield from`, no generics, no runtime type enforcement ◇.
