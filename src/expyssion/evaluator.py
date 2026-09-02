"""AST evaluator. Every expyssion-lambda invocation goes through the machine;
native callables are invoked directly (C-atomic, cannot suspend)."""

from .env import Env
from .errors import UnboundNameError
from .machine import NULL, _Continue, _Return, _Break
from .nodes import (
    Assign, Attr, Block, Call, Cmp, FStr, Infix, Lambda, ListLit, Lit, Name,
    Sub, Tup,
)

import operator as _op

_BINOPS = {
    "+": _op.add, "-": _op.sub, "*": _op.mul, "/": _op.truediv,
    "%": _op.mod, "**": _op.pow, "<<": _op.lshift, ">>": _op.rshift,
    "&": _op.and_, "|": _op.or_, "^": _op.xor,
}
_CMPOPS = {
    "==": _op.eq, "!=": _op.ne, "<": _op.lt, "<=": _op.le,
    ">": _op.gt, ">=": _op.ge,
}


def eval_(node, env, machine):
    t = type(node)
    if t is Lit:
        return node.value
    if t is Name:
        if not env.has(node.id):
            raise UnboundNameError(f"name {node.id!r} is not bound", node.pos)
        return env.lookup(node.id)
    if t is Call:
        return _call(node, env, machine)
    if t is Infix:
        return _BINOPS[node.op](eval_(node.left, env, machine), eval_(node.right, env, machine))
    if t is Cmp:
        left = eval_(node.first, env, machine)
        for op, rn in zip(node.ops, node.rest):
            right = eval_(rn, env, machine)
            if not _CMPOPS[op](left, right):
                return False
            left = right
        return True
    if t is Assign:
        return _assign(node, env, machine)
    if t is Lambda:
        from .interp import ExpysLambda

        return ExpysLambda(node, env, machine)
    if t is Block:
        result = NULL
        for e in node.exprs:
            result = eval_(e, env, machine)
        return result
    if t is ListLit:
        return [eval_(x, env, machine) for x in node.items]
    if t is Tup:
        return tuple(eval_(x, env, machine) for x in node.items)
    if t is Attr:
        return getattr(eval_(node.obj, env, machine), node.name)
    if t is Sub:
        return eval_(node.obj, env, machine)[eval_(node.index, env, machine)]
    if t is FStr:
        return eval(node.raw, {"__builtins__": __builtins__}, env.flatten())
    raise TypeError(f"no evaluator for {t.__name__}")


def _call(node, env, machine):
    head = eval_(node.head, env, machine)
    if getattr(head, "lazy_args", False):
        return head.run_lazy(node, env, machine)
    argv = [eval_(a, env, machine) for a in node.args]
    kwargs = {name: eval_(v, env, machine) for name, v in node.kwargs}
    return invoke(head, argv, kwargs, machine, node.pos)


def invoke(head, argv, kwargs, machine, pos=None):
    if isinstance(head, ExpysLambda):
        return machine.call(head, argv, kwargs, pos)
    if callable(head):
        return head(*argv, **kwargs)
    raise TypeError(f"'{type(head).__name__}' object is not callable")


def _assign(node, env, machine):
    value = eval_(node.value, env, machine)
    if isinstance(node.value, Lambda) and isinstance(value, ExpysLambda):
        value.assigned = True  # born from `=`: its frame catches Return
    target = node.target
    t = type(target)
    if t is Name:
        env.assign(target.id, value)
    elif t is Attr:
        setattr(eval_(target.obj, env, machine), target.name, value)
    elif t is Sub:
        eval_(target.obj, env, machine)[eval_(target.index, env, machine)] = value
    elif t is Tup:
        vals = list(value)
        if len(vals) != len(target.items):
            raise ValueError(f"destructuring mismatch: {len(vals)} values for {len(target.items)} names")
        for name_node, val in zip(target.items, vals):
            env.assign(name_node.id, val)
    else:
        raise TypeError("invalid assignment target")
    return value


from .interp import ExpysLambda  # noqa: E402  (mutual import, needed at call time)
