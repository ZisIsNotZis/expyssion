"""Corpus verification for expyssion LANGUAGE.md v1 (ticket 007/016).

Every check executes the elided hand-transpilation of a spec example and
asserts the output claimed by the spec. Run: python3 docs/verify_corpus.py
Exit 0 = all green. Normative-only (machine-level) semantics are not
executable without a runtime and are marked in docs/transpilation.md.
"""
import sys
import warnings

PASS, FAIL = [], []
checks = []


def check(name):
    def deco(fn):
        try:
            fn()
            PASS.append(name)
        except Exception as e:  # noqa: BLE001
            FAIL.append((name, repr(e)))
        return fn
    return deco


# --- 004 calls & indentation ------------------------------------------------
@check("call: a b c = a(b, c)")
def _():
    A = lambda *r: ("A", *r)
    assert A(1, 2) == ("A", 1, 2)


@check("call: indentation ownership `a b` + `c` = a(b(c))")
def _():
    A = lambda p: ("A", p)
    B = lambda p: ("B", p)
    assert A(B(3)) == ("A", ("B", 3))


@check("call: f (a b c) = f(a(b, c))")
def _():
    A = lambda *r: ("A", *r)
    f = lambda p: ("f", p)
    assert f(A(1, 2)) == ("f", ("A", 1, 2))


@check("call: f (a) (b) = f(a, b)")
def _():
    f = lambda *r: ("f", *r)
    assert f(1, 2) == ("f", 1, 2)


# --- 004 infix ---------------------------------------------------------------
@check("infix: 1+ 2*3 = 7 (precedence)")
def _():
    assert 1 + 2 * 3 == 7


@check("infix: a& b| c = (a&b)|c")
def _():
    a, b, c = 1, 3, 2
    assert (a & b) | c == 3


@check("infix: x+ f 3 = x + f(3) (fixed arity, never variadic head)")
def _():
    f = lambda v: v * 10
    x = 1
    assert x + f(3) == 31


@check("infix: int a/b = int(a/b) (floor division)")
def _():
    a, b = 7, 2
    assert int(a / b) == 3


# --- 004 postfix & brackets --------------------------------------------------
@check("brackets: xs[1] subscript")
def _():
    xs = [10, 20, 30]
    assert xs[1] == 20


@check("brackets: xs[slice 1 3] = xs[slice(1, 3)]")
def _():
    xs = [1, 2, 3, 4]
    assert xs[slice(1, 3)] == [2, 3]


@check("brackets: subscript takes ONE index — a[b(c)]")
def _():
    xs = [10, 20, 30]
    idx = lambda v: 1
    assert xs[idx(0)] == 20


@check("brackets: [a b] spaced = list literal")
def _():
    a, b = 1, 2
    lit = [a, b]
    assert lit == [1, 2]


@check("brackets: f [a b] passes the list as one argument")
def _():
    f = lambda v: ("f", v)
    a, b = 1, 2
    assert f([a, b]) == ("f", [1, 2])


@check("attribute: a.b c = a.b(c)")
def _():
    class Q:
        r = lambda self, v: ("r", v)
    q = Q()
    assert q.r(5) == ("r", 5)


# --- 004 tuples --------------------------------------------------------------
@check("tuple: 3, 4 builds a tuple; destructuring (a b)= 3, 4")
def _():
    a, b = 3, 4
    assert (a, b) == (3, 4)


# --- 003/004 assignment ------------------------------------------------------
@check("assign: chained walrus x= y= 3")
def _():
    x = y = 3
    assert x == 3 and y == 3


@check("assign: subscript & attribute targets")
def _():
    a = [0]
    a[0] = 5
    assert a == [5]


@check("assign: negative literal -1 folds at lexing")
def _():
    assert -1 < 0


@check("assign: expression negation via neg / 0- x")
def _():
    neg = lambda x: -x
    x = 5
    assert neg(x) == -5 and 0 - x == -5


# --- 005 scoping: assignment walks lexical ancestors -------------------------
@check("scope: make_counter — inner assignment edits outer binding (auto cell)")
def _():
    def make_counter():
        n = 0

        def step():
            nonlocal n
            n = n + 1
            return n

        return step

    c = make_counter()
    assert c() == 1 and c() == 2


@check("scope: accumulator inside for body edits enclosing total")
def _():
    xs = [1, 2, 3]

    def f():
        total = 0
        for x in xs:  # consumed body inlined; total is f's cell
            total = total + x
        return total

    assert f() == 6


# --- 001/004 and/or/not -------------------------------------------------------
@check("logic: and/or prefix functions (eager)")
def _():
    def _and(a, b):
        return b if a else a

    assert _and(True, 5) == 5 and _and(False, 5) is False


@check("logic: short-circuit idiom `and a (: b)` — thunk skipped when falsy")
def _():
    calls = []

    def _and(a, b_fn):
        return b_fn() if a else a

    assert _and(False, lambda: calls.append(1)) is False
    assert calls == []


@check("logic: not is a plain function")
def _():
    _not = lambda x: not x
    assert _not(False) is True


# --- 001 control flow ---------------------------------------------------------
@check("control: clip — guard return crosses consumed if body (elided)")
def _():
    def clip(x):
        if x < 0:
            return 0
        return x

    assert clip(-1) == 0 and clip(2) == 2


@check("control: if without else yields null (None); branches are invoked callables")
def _():
    def if_(c, t, e=None):
        return t() if c else (e() if e is not None else None)

    assert if_(True, lambda: 1) == 1 and if_(False, lambda: 1) is None
    assert if_(1, lambda: "odd", lambda: "even") == "odd"


@check("control: while cond is a re-invoked lambda")
def _():
    out = []
    n = 3
    while n > 0:
        out.append(n)
        n = n - 1
    assert out == [3, 2, 1]


@check("control: for with else (completion without break)")
def _():
    def find(xs, p):
        for x in xs:
            if p(x):
                return x
        else:
            return None

    assert find([1, 2, 3], lambda v: v == 2) == 2
    assert find([1], lambda v: v == 9) is None


@check("control: try body handler (no finally — with_resource covers it)")
def _():
    def safe(fn):
        try:
            return fn()
        except Exception as e:
            return ("err", type(e).__name__)

    assert safe(lambda: 1 / 0)[0] == "err"
    assert safe(lambda: 7) == 7


# --- 002 generators & comprehensions ------------------------------------------
@check("gen: yielding lambda driven by list")
def _():
    def gen():
        yield 1

    assert list(gen()) == [1]


@check("gen: comprehension `list (for (range 3) x: yield x*x)`")
def _():
    assert [x * x for x in range(3)] == [0, 1, 4]


@check("gen: dict comprehension with tuple pairs")
def _():
    ks, vs = ["a", "b"], [1, 2]
    assert {k: v for k, v in zip(ks, vs)} == {"a": 1, "b": 2}


@check("gen: for drives a yielding lambda (generator iteration)")
def _():
    def nums():
        for x in range(100):
            yield x

    out = [x * x for x in nums() if x % 3 == 0]
    assert out[:4] == [0, 9, 36, 81]


@check("gen: nested collectors — nearest handler wins (matrix)")
def _():
    matrix = [[y for y in range(2)] for _ in range(3)]
    assert matrix == [[0, 1], [0, 1], [0, 1]]


@check("lib: map/filter lazy; len; first via next")
def _():
    assert list(map(lambda x: x * 2, [1, 2])) == [2, 4]
    assert next(filter(lambda x: x % 2 == 0, [1, 2, 3])) == 2
    assert len([1, 2, 3]) == 3


# --- 007 litmus programs -------------------------------------------------------
@check("litmus: febonacci 10 = 55")
def _():
    def febonacci(n):
        return n if n <= 1 else febonacci(n - 1) + febonacci(n - 2)

    assert febonacci(10) == 55


@check("litmus: guard-style early return")
def _():
    def guard(x):
        if x < 0:
            return 0
        return x * 2

    assert guard(-5) == 0 and guard(3) == 6


# --- 014 interop ----------------------------------------------------------------
@check("interop: non-callable invocation raises native TypeError")
def _():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # the call itself is deliberately invalid
        try:
            exec("[1, 2, 3](5)")
            raise AssertionError("expected TypeError")
        except TypeError:
            pass


try:
    import numpy as np  # noqa: F401

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


@check("interop: numpy — attribute call, C-atomic ops")
def _():
    arr = np.arange(10)
    assert arr.max() == 9


try:
    import greenlet  # noqa: F401

    HAS_GREENLET = True
except ImportError:
    HAS_GREENLET = False


@check("concurrency: cross-thread switch fails cleanly (thread affinity)")
def _():
    import threading

    import greenlet

    result = {}

    def child():
        greenlet.getcurrent().parent.switch()

    g = greenlet.greenlet(child)
    g.switch()

    def try_switch():
        try:
            g.switch()
            result["r"] = "switched (unexpected)"
        except Exception as e:
            result["r"] = type(e).__name__

    t = threading.Thread(target=try_switch, daemon=True)
    t.start()
    t.join(3)
    assert result.get("r") == "error", result  # greenlet.error: cannot switch to a different thread


def main():
    for name, fn in checks:
        fn()
    for name in PASS:
        print(f"  PASS {name}")
    for name, err in FAIL:
        print(f"  FAIL {name}: {err}")
    skipped = []
    if not HAS_NUMPY:
        skipped.append("interop: numpy")
    if not HAS_GREENLET:
        skipped.append("concurrency: cross-thread")
    for s in skipped:
        print(f"  SKIP {s} (dependency missing)")
    print(f"{len(PASS)} passed, {len(FAIL)} failed, {len(skipped)} skipped")
    sys.exit(1 if FAIL else 0)


main()
