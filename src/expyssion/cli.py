"""`expy` — the expyssion CLI. Usage: expy run program.expy (run is default)."""

import sys

from .api import run_source
from .errors import ExpyssionError


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: expy run <file.expy>")
        return 0
    cmd = argv[0]
    if cmd == "run":
        argv = argv[1:]
    if not argv:
        print("error: no program file given", file=sys.stderr)
        return 2
    path = argv[0]
    try:
        run_source(open(path, "r", encoding="utf-8").read())
    except ExpyssionError as e:
        print(f"expyssion error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
