"""Public entry: run expyssion source."""

from .env import Env
from .errors import ExpyssionError
from .evaluator import eval_
from .machine import NULL, Machine, _Break, _Continue, _Return
from .parser import parse
from .stdlib import make_builtins


def run_source(source, machine=None):
    """Parse + execute expyssion source; returns the program's last value."""
    import sys

    # chain depth: frozen greenlet frames share the thread recursion counter
    # (substrate fact) — the runtime raises the documented limit
    if sys.getrecursionlimit() < 200_000:
        sys.setrecursionlimit(200_000)
    machine = machine or Machine()
    program = parse(source)
    genv = Env(parent=make_builtins(machine))
    try:
        result = NULL
        for expr in program.exprs:
            result = eval_(expr, genv, machine)
        return result
    except (_Return, _Break, _Continue) as exc:
        raise Machine.translate_escaped(exc) from exc


def run_file(path, machine=None):
    with open(path, "r", encoding="utf-8") as f:
        return run_source(f.read(), machine)


__all__ = ["run_source", "run_file", "Machine", "ExpyssionError"]
