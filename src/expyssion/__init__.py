"""expyssion — everything is an expression; everything is a call."""

from .api import Machine, run_file, run_source
from .errors import ExpyssionError

__version__ = "0.1.0"
__all__ = ["run_source", "run_file", "Machine", "ExpyssionError"]
