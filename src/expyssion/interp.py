"""ExpysLambda: a lambda value. Assigned lambdas (born from `=`) catch Return;
consumed ones are transparent. Exposed to Python as a callable and iterable."""

from .env import Env
from .evaluator import eval_
from .machine import NULL, YieldMsg, _Return
from .nodes import Block


class ParamArityError(TypeError):
    pass


class ExpysLambda:
    __slots__ = ("node", "def_env", "machine", "assigned")

    def __init__(self, node, def_env, machine, assigned=False):
        self.node = node
        self.def_env = def_env
        self.machine = machine
        self.assigned = assigned

    def _split_params(self):
        pre, post, star, dstar = [], [], None, None
        seen_star = False
        for p in self.node.params:
            if p.name == ":ret":
                continue  # return annotation is documentation-only
            if p.star:
                star, seen_star = p, True
            elif p.dstar:
                dstar = p
            elif seen_star:
                post.append(p)
            else:
                pre.append(p)
        return pre, post, star, dstar

    def invoke(self, argv, kwargs, machine):
        env = Env(self.def_env)
        pre, post, star, dstar = self._split_params()
        args = list(argv)
        kw = dict(kwargs)

        i = 0
        for p in pre:
            if i < len(args):
                env.assign(p.name, args[i])
                i += 1
            elif p.name in kw:
                env.assign(p.name, kw.pop(p.name))
            elif p.default is not None:
                env.assign(p.name, eval_(p.default, self.def_env, machine))
            else:
                raise ParamArityError(
                    f"lambda is missing required argument {p.name!r}")
        rest = args[i:]
        if rest and star is None:
            raise ParamArityError(
                f"lambda takes {len(pre)} positional arguments but {len(argv)} were given")
        if star is not None:
            env.assign(star.name, tuple(rest))
        for p in post:  # keyword-only (declared after ..)
            if p.name in kw:
                env.assign(p.name, kw.pop(p.name))
            elif p.default is not None:
                env.assign(p.name, eval_(p.default, self.def_env, machine))
            else:
                raise ParamArityError(f"lambda is missing argument {p.name!r}")
        if kw:
            if dstar is not None:
                env.assign(dstar.name, kw)
            else:
                raise ParamArityError(f"unexpected keyword arguments: {sorted(kw)}")

        try:
            body = self.node.body
            if isinstance(body, Block):
                result = NULL
                for e in body.exprs:
                    result = eval_(e, env, machine)
                return result
            return eval_(body, env, machine)
        except _Return as r:
            if self.assigned:
                return r.value
            raise

    # --- Python interop: auto context (plain call; yields are loud) ---
    def __call__(self, *args, **kwargs):
        return self.machine.call(self, list(args), kwargs)

    def __iter__(self):
        return _driven_iter(self, self.machine)

    def __repr__(self):
        return f"<expyssion lambda{' assigned' if self.assigned else ''} {id(self):#x}>"


def _driven_iter(fn, machine):
    """Python-side driver: yields values; closing the iterator throws
    GeneratorExit into the suspended chain (driver-owned cleanup)."""
    g = machine.spawn(lambda: fn.invoke([], {}, machine))
    msg = g.switch()
    while isinstance(msg, YieldMsg):
        try:
            sent = yield msg.value
        except GeneratorExit:
            g.throw(GeneratorExit)
            raise
        msg = msg.src.g.switch(sent)
    # Done — completion value surfaces as StopIteration (dropped by `for`)
