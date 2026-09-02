"""Lexer: tokens carry a `glued` flag (no whitespace between previous token and
this one). The glue rule is enforced here for infix symbols; `=`/`:`/brackets
are hard-wired syntax and parse-position-sensitive instead.

- Negative literals fold at lexing: a `-` that starts a token and is followed
  by a digit is part of the number. A detached `-` (token start, non-digit) is
  a syntax error — a detached minus is never an operator.
- Literals adopt Python syntax (strings incl. f-strings, ints, floats).
- `#` starts a comment. One expression per line; indentation is structural.
"""

from .errors import ExpyssionSyntaxError

MULTI_OPS = (":=", "==", "!=", "<=", ">=", "<<", ">>", "**")
SINGLE_OPS = set("+-*/%&|^<>=")
PUNCT = set("()[],.:")
NAME_START = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
NAME_CHARS = NAME_START | set("0123456789")


class Token:
    __slots__ = ("type", "value", "line", "col", "glued")

    def __init__(self, type, value, line, col, glued):
        self.type = type
        self.value = value
        self.line = line
        self.col = col
        self.glued = glued

    def __repr__(self):
        return f"Token({self.type},{self.value!r},glued={self.glued})"


def lex(source):
    toks = []
    indents = [0]
    lines = source.expandtabs(4).split("\n")
    for lineno, raw in enumerate(lines, 1):
        line, col = _strip_comment(raw), 0
        stripped = line.strip()
        if not stripped:
            continue  # blank / comment-only lines carry no structure
        indent = len(line) - len(line.lstrip(" "))
        if indent > indents[-1]:
            indents.append(indent)
            toks.append(Token("INDENT", " " * indent, lineno, 1, False))
        else:
            while indent < indents[-1]:
                indents.pop()
                toks.append(Token("DEDENT", "", lineno, 1, False))
            if indent != indents[-1]:
                raise ExpyssionSyntaxError("unindent does not match any outer level", (lineno, 1))
        _lex_line(stripped, lineno, indent + 1, toks)
        toks.append(Token("NEWLINE", "\n", lineno, len(line) + 1, False))
    while len(indents) > 1:
        indents.pop()
        toks.append(Token("DEDENT", "", len(lines), 1, False))
    toks.append(Token("EOF", "", len(lines) + 1, 1, False))
    return toks


def _strip_comment(line):
    in_str = None
    i = 0
    while i < len(line):
        c = line[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == in_str:
                in_str = None
        elif c in "\"'":
            in_str = c
        elif c == "#":
            return line[:i]
        i += 1
    return line


def _lex_line(line, lineno, startcol, toks):
    i, n = 0, len(line)
    while i < n:
        c = line[i]
        if c == " ":
            i += 1
            prev_glued = False
            continue
        col = startcol + i
        glued = _prev_ends_adjacent(line, i)
        if c in "\"'" or (c in "fF" and i + 1 < n and line[i + 1] in "\"'"):
            j = _scan_string(line, i, lineno)
            text = line[i:j]
            if text[0] in "fF":
                toks.append(Token("FSTR", text, lineno, col, glued))
            else:
                import ast as _ast

                toks.append(Token("STR", _ast.literal_eval(text), lineno, col, glued))
            i = j
        elif c.isdigit() or (c == "-" and i + 1 < n and line[i + 1].isdigit()):
            j = _scan_number(line, i)
            text = line[i:j]
            value = float(text) if ("." in text or "e" in text or "E" in text) else int(text)
            toks.append(Token("NUM", value, lineno, col, glued))
            i = j
        elif c == "-" and glued is False:
            raise ExpyssionSyntaxError("detached '-' is not an operator; use `0- x`, `neg x`, or a literal like -1", (lineno, col))
        elif c.isalpha() or c == "_":
            j = i + 1
            while j < n and line[j] in NAME_CHARS:
                j += 1
            toks.append(Token("NAME", line[i:j], lineno, col, glued))
            i = j
        else:
            two = line[i:i + 2]
            if two in MULTI_OPS:
                _require_glued(two, glued, lineno, col)
                toks.append(Token("OP", two, lineno, col, glued))
                i += 2
                continue
            if c in SINGLE_OPS:
                _require_glued(c, glued, lineno, col)
                toks.append(Token("OP", c, lineno, col, glued))
                i += 1
                continue
            if c == ".":
                j = i
                while j < n and line[j] == ".":
                    j += 1
                ndots = j - i
                if ndots == 1:
                    _require_glued(".", glued, lineno, col)
                    toks.append(Token("OP", ".", lineno, col, glued))
                elif ndots in (2, 3):
                    toks.append(Token("PUNCT", "." * ndots, lineno, col, glued))
                else:
                    raise ExpyssionSyntaxError("too many dots", (lineno, col))
                i = j
                continue
            if c in PUNCT:
                toks.append(Token("PUNCT", c, lineno, col, glued))
                i += 1
                continue
            raise ExpyssionSyntaxError(f"unexpected character {c!r}", (lineno, col))


def _require_glued(op, glued, lineno, col):
    if not glued:
        raise ExpyssionSyntaxError(
            f"operator {op!r} must be glued to its left operand", (lineno, col))


def _prev_ends_adjacent(line, i):
    """True when the character before i is part of the previous token (no space)."""
    return i > 0 and line[i - 1] != " "


def _scan_string(line, i, lineno):
    q = line[i + 1] if line[i] in "fF" else line[i]
    start = i + 1 if line[i] in "fF" else i
    j = start + 1
    n = len(line)
    while j < n:
        if line[j] == "\\":
            j += 2
            continue
        if line[j] == q:
            return j + 1
        j += 1
    raise ExpyssionSyntaxError("unterminated string", (lineno, i + 1))


def _scan_number(line, i):
    j = i
    if line[j] == "-":
        j += 1
    n = len(line)
    while j < n and (line[j].isdigit() or line[j] in ".eE"):
        if line[j] in "eE" and j + 1 < n and line[j + 1] in "+-":
            j += 2
            continue
        j += 1
    return j
