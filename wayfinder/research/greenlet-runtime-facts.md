# Greenlet runtime facts (ticket: Greenlet runtime facts)

Date: 2025-09-01 · Environment for empirical tests: greenlet 3.2.5, CPython 3.9.25, Linux x86_64. Docs fetched from <https://greenlet.readthedocs.io/en/latest/> (pages: greenlet_gc, caveats, tracing, python_threads). Test scripts were scratch venv scripts, reproducible from the quoted snippets.

## 1. GreenletExit and last-reference cleanup

- Docs (greenlet_gc): if all references to a greenlet go away — including references from other greenlets' `parent` attributes — "there is no way to ever switch back to this greenlet. In this case, a GreenletExit exception is generated into the greenlet. This is the only case where a greenlet receives the execution asynchronously." It gives `try/finally` a chance to clean up.
- Docs: the greenlet "is expected to either die or be resurrected"; "just catching and ignoring the GreenletExit is likely to lead to an infinite loop" — runtime handlers must not swallow it.
- Implication for expyssion: abandoned generator chains run their `finally` blocks at GC time, nondeterministically; explicit `close` (throw `GeneratorExit`-style) stays the deterministic path.

## 2. Garbage collection: leaks through cycles are real (verified empirically)

- Docs warning (greenlet_gc): "Greenlets participate in garbage collection in a limited fashion; cycles involving data that is present in a greenlet's frames may not be detected."
- Empirical: an unreachable suspended chain whose frame data participates in a reference cycle (`g1._cyc = [bomb, g1]`) was **not** collected after `gc.collect()` — the bomb's `__del__` never ran. A non-cyclic unreachable suspended chain **was** collected.
- Implication: reference-dense S1⁺ chains (each frame holds its child greenlet) plus user data cycles can leak. The close/cancellation ticket must make explicit close normative and document the cyclic-data hazard.

## 3. Thread affinity

- Docs (python_threads): "each thread contains an independent 'main' greenlet with a tree of sub-greenlets. It is not possible to mix or switch between greenlets belonging to different threads."
- Empirical: switching from a non-owning thread raises a clean `greenlet.error: cannot switch to a different thread` (the target greenlet survives, `dead` is False).
- Implication: a suspended chain (generator) may only be resumed on its owning thread; a thread-per-generator fallback using queues is viable for a stdlib-only runtime.

## 4. Tracing and profiling

- Docs (tracing): "Standard Python tracing and profiling doesn't work as expected when used with greenlet since stack and frame switching happens on the same Python thread." greenlet provides `settrace(callback)` with `switch` and `throw` events, `args=(origin, target)`; the callback runs in the target greenlet's context and exceptions replace the switch with a throw.
- py-spy: no greenlet/gevent support claim found in the upstream README (checked 2025-09-01) — earlier assumption of py-spy support is **unverified**; do not rely on it in the spec.
- Implication: the traceback/error ticket must design presentation on top of `greenlet.settrace`, not assume stock tooling.

## 5. Recursion depth is NOT lifted (falsified a charting-time claim)

- Empirical: a chain of per-call greenlets (each `call()` frame staying live while its child runs) hit `RecursionError` with `sys.setrecursionlimit(300)` at modest depth; normal recursion failed identically. greenlet does **not** reset CPython's per-thread recursion counter across switches.
- The same test revealed the traceback shape: **frames from every greenlet in the chain concatenate into one traceback** — complete but potentially enormous for deep chains.
- Implication: S1⁺ chain depth is still bounded by the recursion limit divided by frames-per-level. The runtime must raise/manage the limit and the spec must state the bound honestly. This corrects ADR 0001's "recursion depth is no longer bounded by Python's stack limit" claim (edited there).

## 6. Performance (this machine, order-of-magnitude)

- Empirical microbenchmarks: spawn + switch to an immediately-returning leaf ≈ **867 ns**; two-way ping-pong switch ≈ **666 ns** per round trip. No Result-object allocation included.
- Implication: 10–50× call overhead before elision is the right planning number; elision remains essential, not optional.

## 7. Exception propagation across switches

- Empirical: a `ValueError` raised in a child greenlet propagated through `parent.switch()` with a clean, naturally chained traceback (caller frames + child frames inline, no artifact frames beyond the `call()` site).
- Implication: better than feared for shallow chains; the cost shows up as traceback *length* for deep chains (§5), which is an error-message-design input, not a correctness problem.

## 8. Free-threaded CPython

- Docs (caveats): greenlet ≥3.3.0 supports Python 3.14 free-threading, marked experimental with "limited testing"; known issues include fork hazards ("Greenlet maintains internal locks and forking at the wrong time might result in the child process hanging"), GC differences where "GreenletExit may no longer be raised", possible leaks, and a bytecode-cache crash workaround (`PYTHON_TLBC=0`).

## 9. C extensions and re-entrancy

- Docs (caveats): "Native Functions Should Be Re-entrant … if the library function is not re-entrant, and more than one greenlet attempts to enter it, subtle problems can result" — the cited incident is gevent corrupting libuv's internal state.
- Issue trackers: no correctness issue found for numpy+greenlet (nearest: gevent#1891, spurious numpy warnings, closed). expyssion's design never switches inside C code, so C operations are atomic; the residual hazard is C state (static buffers, handles) held across a suspension point, and C→Python callback seams.
