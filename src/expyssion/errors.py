"""Normative loud-error vocabulary (LANGUAGE.md §12). All carry expyssion source position."""


class ExpyssionError(Exception):
    def __init__(self, message, pos=None):
        self.pos = pos
        if pos is not None:
            message = f"{message} (line {pos[0]}, col {pos[1]})"
        super().__init__(message)


class UnhandledYieldError(ExpyssionError):
    """unhandled yield outside generator context"""


class ReturnOutsideFunctionError(ExpyssionError):
    """return outside function (no assigned lambda frame above)"""


class BreakOutsideLoopError(ExpyssionError):
    """break outside loop"""


class ContinueOutsideLoopError(ExpyssionError):
    """continue outside loop"""


class CloseOfNonGeneratorError(ExpyssionError):
    """close of non-generator"""


class CollectorShapeError(ExpyssionError):
    """collector wrong-shape / wrong arity"""


class UnboundNameError(ExpyssionError, NameError):
    """name is not bound in any lexical ancestor"""


class ExpyssionSyntaxError(ExpyssionError, SyntaxError):
    """surface-syntax violation (glue rule, indentation, etc.)"""
