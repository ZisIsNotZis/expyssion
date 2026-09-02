"""Lexical environments: chain of bindings with a builtins boundary.

Assignment edits the nearest lexical ancestor binding (auto closure cells) and
never edits the builtins layer — shadowing a builtin defines locally.
"""


class Env:
    __slots__ = ("bindings", "parent", "is_builtins")

    def __init__(self, parent=None, is_builtins=False):
        self.bindings = {}
        self.parent = parent
        self.is_builtins = is_builtins

    def lookup(self, name):
        env = self
        while env is not None:
            b = env.bindings
            if name in b:
                return b[name]
            env = env.parent
        return None  # caller converts to loud UnboundNameError

    def has(self, name):
        env = self
        while env is not None:
            if name in env.bindings:
                return True
            env = env.parent
        return False

    def assign(self, name, value):
        """Edit nearest lexical ancestor binding (auto cell); builtins layer is
        a boundary — define locally instead of mutating builtins."""
        env = self
        while env is not None:
            if name in env.bindings:
                if env.is_builtins:
                    break
                env.bindings[name] = value
                return
            env = env.parent
        self.bindings[name] = value

    def flatten(self):
        """Materialize the full chain (builtins included) into one dict — used
        by f-string evaluation."""
        out = {}
        chain = []
        env = self
        while env is not None:
            chain.append(env)
            env = env.parent
        for env in reversed(chain):
            out.update(env.bindings)
        return out
