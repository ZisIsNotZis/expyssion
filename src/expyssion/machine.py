"""The sync-point effect machine (ADR 0001), implemented literally on greenlets.

- Every invocation of an expyssion lambda runs in a fresh greenlet (a sync
  point). Native Python callables are invoked directly: they cannot suspend,
  so no sync point is needed (as-if clause).
- Upward channel: the private `YieldMsg` wrapper or a bare completion value,
  plus native exceptions. Downward: start arguments or resume values.
- `return`/`break`/`continue` are BaseException subclasses; assigned lambda
  frames catch _Return, loop drivers catch _Break/_Continue.
- Unwinds are exception-safe: every spawned child is tracked and thrown
  GeneratorExit (running finallys) when its frame exits abnormally.
"""

import greenlet
import threading

from .errors import (
    BreakOutsideLoopError,
    ContinueOutsideLoopError,
    ReturnOutsideFunctionError,
    UnhandledYieldError,
)


class YieldMsg:
    """Private upward wrapper for a yield. `vouched` marks yields forwarded by
    a driver (comprehension-worthy); unvouched yields reaching a collector are
    loud."""

    __slots__ = ("value", "src", "vouched")

    def __init__(self, value, src, vouched=False):
        self.value = value
        self.src = src
        self.vouched = vouched


class _Return(BaseException):
    def __init__(self, value):
        self.value = value


class _Break(BaseException):
    pass


class _Continue(BaseException):
    pass


class Machine:
    def __init__(self):
        self._tls = threading.local()

    @property
    def _children(self):
        d = getattr(self._tls, "children", None)
        if d is None:
            d = self._tls.children = {}
        return d

    # --- plain call: yields become loud or chain upward ---------------
    def call(self, fn, argv, kwargs=None, pos=None, vouch=False):
        g = greenlet.greenlet(self._runner(fn, argv, kwargs or {}, pos))
        self._track(g)
        msg = g.switch()
        if isinstance(msg, YieldMsg):
            if vouch:
                msg.vouched = True
            return self._chain_up(msg)
        return msg

    def _chain_up(self, msg):
        cur = greenlet.getcurrent()
        if cur.parent is None:
            # no handler above: unwind the suspended chain loudly (finallys run)
            err = UnhandledYieldError(
                "unhandled yield outside generator context",
                getattr(msg.src, "pos", None),
            )
            msg.src.g.throw(err)  # re-raises here when the chain has unwound
            raise err  # reached only if the yielder swallowed the throw
        return cur.parent.switch(msg)

    def _runner(self, fn, argv, kwargs, pos):
        def run():
            cur = greenlet.getcurrent()
            try:
                return fn.invoke(argv, kwargs, self)
            finally:
                self._kill_children(cur)
        return run

    # --- driver primitives (collectors / loops) ------------------------
    def spawn(self, run):
        g = greenlet.greenlet(self._wrap(run))
        self._track(g)
        return g

    def _wrap(self, run):
        def wrapper():
            cur = greenlet.getcurrent()
            try:
                return run()
            finally:
                self._kill_children(cur)
        return wrapper

    def _track(self, g):
        cur = greenlet.getcurrent()
        self._children.setdefault(cur, []).append(g)

    def _kill_children(self, cur):
        kids = self._children.pop(cur, None)
        if not kids:
            return
        for k in kids:
            if k:
                try:
                    k.throw(GeneratorExit)
                except BaseException:
                    pass

    # --- effects (called from evaluator builtins) -----------------------
    def yield_effect(self, value, pos=None, vouch=False):
        cur = greenlet.getcurrent()
        if cur.parent is None:
            raise UnhandledYieldError("unhandled yield outside generator context", pos)
        return cur.parent.switch(YieldMsg(value, _Yielder(cur, pos), vouch))

    def return_effect(self, value, pos=None):
        raise _Return(value)

    def break_effect(self, pos=None):
        raise _Break()

    def continue_effect(self, pos=None):
        raise _Continue()

    # --- loud errors for escaped control signals ------------------------
    @staticmethod
    def translate_escaped(exc, pos=None):
        if isinstance(exc, _Return):
            return ReturnOutsideFunctionError("return outside function", pos)
        if isinstance(exc, _Break):
            return BreakOutsideLoopError("break outside loop", pos)
        if isinstance(exc, _Continue):
            return ContinueOutsideLoopError("continue outside loop", pos)
        return exc


class _Yielder:
    """Identifies the yielding greenlet for resume targeting."""

    __slots__ = ("g", "pos")

    def __init__(self, g, pos):
        self.g = g
        self.pos = pos


NULL = None  # null is Python None — interop-friendly by construction
