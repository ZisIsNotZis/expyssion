"""The v1 standard library (LANGUAGE.md §9).

Control structures are ordinary functions. Collectors (`list`/`dict`/`set`)
and `try` are lazy-argument builtins: they receive the AST node and evaluate
arguments inside a driven greenlet, which is what makes comprehension yields
land in their handler. Everything else takes plain values.

`return`/`break`/`continue`/`yield` are effect functions bound per-machine.
"""

import importlib

from .errors import CollectorShapeError, UnhandledYieldError
from .evaluator import eval_, invoke
from .interp import ExpysLambda
from .machine import NULL, YieldMsg, _Break, _Continue


class LazyBuiltin:
    """A builtin that evaluates its own arguments (needs AST + env)."""

    lazy_args = True

    def __init__(self, name, run_lazy):
        self.name = name
        self._run = run_lazy

    def run_lazy(self, node, env, machine):
        return self._run(node, env, machine)

    def __repr__(self):
        return f"<builtin {self.name}>"


# --- collectors -----------------------------------------------------------

def _collector(kind):
    def run(node, env, machine):
        if len(node.args) != 1 or node.kwargs:
            raise CollectorShapeError(f"{kind} takes exactly one argument", node.pos)
        g = machine.spawn(lambda: eval_(node.args[0], env, machine))
        msg = g.switch()
        vals = []
        while isinstance(msg, YieldMsg):
            if not msg.vouched:
                err = UnhandledYieldForCollector(
                    "unhandled yield outside generator context", node.pos)
                g.throw(err)  # unwinds the driven subtree; re-raises here
                raise err
            vals.append(msg.value)
            msg = g.switch(NULL)
        value = msg
        if isinstance(value, ExpysLambda):
            dvals, _ = _drive_collect(value, machine)
            vals.extend(dvals)
        if kind == "list":
            if vals:
                return list(vals)
            if hasattr(value, "__iter__"):
                return list(value)
            return [value]
        if kind == "set":
            if vals:
                return set(vals)
            if hasattr(value, "__iter__"):
                return set(value)
            return {value}
        # dict
        if vals:
            return _pairs(vals, node.pos)
        if isinstance(value, dict):
            return dict(value)
        if hasattr(value, "__iter__"):
            return _pairs(list(value), node.pos)
        raise CollectorShapeError("dict needs key/value pairs", node.pos)
    return LazyBuiltin(kind, run)


def _pairs(vals, pos):
    out = {}
    for v in vals:
        try:
            k, v2 = v
        except (TypeError, ValueError):
            raise CollectorShapeError(f"dict pair has wrong shape: {v!r}", pos) from None
        out[k] = v2
    return out


class UnhandledYieldForCollector(UnhandledYieldError):
    pass


def _drive_collect(fn, machine):
    g = machine.spawn(lambda: fn.invoke([], {}, machine))
    msg = g.switch()
    vals = []
    while isinstance(msg, YieldMsg):
        vals.append(msg.value)
        msg = msg.src.g.switch(NULL)
    return vals, msg


list_ = _collector("list")
dict_ = _collector("dict")
set_ = _collector("set")


# --- loops ------------------------------------------------------------------

def _body_arity(fn):
    if isinstance(fn, ExpysLambda):
        pre, post, star, dstar = fn._split_params()
        return len(pre)
    return 1


def for_(iterable, body, else_=None, machine=None):
    if machine is None:
        raise TypeError("for needs a machine")
    last = NULL
    broke = False

    def call_body(v):
        n = _body_arity(body)
        if n > 1 and isinstance(v, (tuple, list)) and len(v) == n:
            return machine.call(body, list(v), vouch=True)
        return machine.call(body, [v] if n == 1 else [], vouch=True)

    if isinstance(iterable, ExpysLambda):
        g = machine.spawn(lambda: iterable.invoke([], {}, machine))
        msg = g.switch()
        while isinstance(msg, YieldMsg):
            try:
                last = call_body(msg.value)
            except _Break:
                broke = True
            except _Continue:
                pass
            if broke:
                break
            msg = msg.src.g.switch(NULL)
        if broke:
            g.throw(GeneratorExit)
    else:
        for v in iterable:
            try:
                last = call_body(v)
            except _Break:
                broke = True
                break
            except _Continue:
                continue
    if not broke and else_ is not None:
        invoke(else_, [], {}, machine)
    return last


def while_(cond, body, else_=None, machine=None):
    if machine is None:
        raise TypeError("while needs a machine")
    last = NULL
    broke = False
    while machine.call(cond, []):
        try:
            last = machine.call(body, [], vouch=True)
        except _Break:
            broke = True
            break
        except _Continue:
            continue
    if not broke and else_ is not None:
        invoke(else_, [], {}, machine)
    return last


def if_(c, t, e=None, machine=None):
    branch = t if c else e
    if branch is None:
        return NULL
    return invoke(branch, [], {}, machine)


def try_(node, env, machine):
    try:
        return eval_(node.args[0], env, machine)
    except Exception as e:
        if len(node.args) > 1:
            handler = eval_(node.args[1], env, machine)
            return invoke(handler, [e], {}, machine)
        raise


def raise_(exc=None):
    if exc is None:
        raise TypeError("raise needs an exception instance (re-raise with `raise e`)")
    if not isinstance(exc, BaseException):
        raise TypeError("raise needs an exception instance")
    raise exc


def with_resource_(acquire, body, machine=None):
    r = invoke(acquire, [], {}, machine)
    if hasattr(r, "__enter__"):
        with r:
            return invoke(body, [r], {}, machine)
    try:
        return invoke(body, [r], {}, machine)
    finally:
        closer = getattr(r, "close", None)
        if callable(closer):
            closer()


# --- sequences & values ------------------------------------------------------

def map_(f, xs, machine=None):
    def gen():
        for x in xs:
            yield invoke(f, [x], {}, machine)
    return gen()


def filter_(pred, xs, machine=None):
    def gen():
        for x in xs:
            if invoke(pred, [x], {}, machine):
                yield x
    return gen()


def first_(x, machine=None):
    if isinstance(x, ExpysLambda):
        it = iter(x)
        try:
            return next(it)
        finally:
            it.close()
    return next(iter(x))


def import_(name):
    if not isinstance(name, str):
        raise TypeError('import takes a module-name string: import "numpy"')
    return importlib.import_module(name)


def and_(a, b):
    return b if a else a


def or_(a, b):
    return a if a else b


def not_(a):
    return not a


def neg(x):
    return -x


def _effect(machine):
    def return_(v=NULL):
        machine.return_effect(v)

    def break_():
        machine.break_effect()

    def continue_():
        machine.continue_effect()

    def yield_(v=NULL):
        return machine.yield_effect(v)

    return {"return": return_, "break": break_, "continue": continue_, "yield": yield_}


def make_builtins(machine):
    """One builtins Env per machine (effects capture it)."""
    from .env import Env

    b = Env(is_builtins=True)
    plain = {
        "if": lambda c, t, e=None: if_(c, t, e, machine),
        "while": lambda c, body, e=None: while_(c, body, e, machine),
        "for": lambda it, body, e=None: for_(it, body, e, machine),
        "try": LazyBuiltin("try", try_),
        "raise": raise_,
        "with_resource": lambda acq, body: with_resource_(acq, body, machine),
        "list": list_, "dict": dict_, "set": set_,
        "and": and_, "or": or_, "not": not_,
        "return": None, "break": None, "continue": None, "yield": None,
        "import": import_,
        "map": lambda f, xs: map_(f, xs, machine),
        "filter": lambda pred, xs: filter_(pred, xs, machine),
        "first": lambda x: first_(x, machine),
        "neg": neg,
        "range": range, "zip": zip, "len": len, "sorted": sorted,
        "enumerate": enumerate, "reversed": reversed, "sum": sum,
        "min": min, "max": max, "abs": abs,
        "print": print, "str": str, "int": int, "float": float,
        "isinstance": isinstance, "getattr": getattr, "slice": slice,
        "null": None, "None": None, "True": True, "False": False,
    }
    effects = _effect(machine)
    plain.update(effects)
    b.bindings = plain
    return b
