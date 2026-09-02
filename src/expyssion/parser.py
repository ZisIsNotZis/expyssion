"""Recursive-descent parser for expyssion (LANGUAGE.md §1–§5).

Key mechanisms:
- Line ownership: the last unit (rightmost primary+postfix expression) of a
  line owns following deeper-indented lines as additional arguments — `a b`
  with indented `c` is a(b(c)); `a` with indented `b`, `c` is a(b, c).
- Lambda: `: body` (zero params), `x: body` (one bare param), or a paren
  group followed by a glued colon for the full param grammar
  (`(a:int b:int= 2 .. ... :ret)`).
- Call-site kwargs: `name:=value` (glued), very high precedence.
- Assignment is an operand-level construct: a glued `=` after a Name/Attr/Sub
  (or a names-only paren group = destructuring) is Assign; in expression
  position this is the walrus. Assignment RHS parses greedily (chains).
- Bracket duality: glued `[ ]` = subscript (one index expr); spaced `[ … ]`
  = list literal (space-separated elements).
- Tuples: `,` glued to its left element, lowest precedence.
"""

from .errors import ExpyssionSyntaxError as ParseError
from .lexer import lex
from .nodes import (
    Assign, Attr, Block, Call, Cmp, FStr, Infix, Lambda, ListLit, Lit, Name,
    Param, Sub, Tup,
)

INFIX_BP = {
    "**": 90, "*": 80, "/": 80, "%": 80,
    "+": 70, "-": 70, "<<": 60, ">>": 60,
    "&": 50, "^": 45, "|": 40,
    "==": 30, "!=": 30, "<": 30, "<=": 30, ">": 30, ">=": 30,
}
CMP_OPS = {"==", "!=", "<", "<=", ">", ">="}
ARG_STARTERS = {"NAME", "NUM", "STR", "FSTR"}


class Parser:
    def __init__(self, tokens):
        self.toks = tokens
        self.i = 0
        self._last_unit = None
        self._line_broken = False  # a block-bodied lambda ended the line

    # --- token helpers ---
    def peek(self, k=0):
        j = min(self.i + k, len(self.toks) - 1)
        return self.toks[j]

    def next(self):
        t = self.toks[self.i]
        if t.type != "EOF":
            self.i += 1
        return t

    def at(self, type, value=None):
        t = self.peek()
        return t.type == type and (value is None or t.value == value)

    def eat(self, type, value=None):
        if self.at(type, value):
            return self.next()
        return None

    def err(self, msg):
        t = self.peek()
        raise ParseError(msg, (t.line, t.col))

    # --- entry ---
    def parse_program(self):
        exprs = self._parse_lines(top=True)
        return Block(exprs=exprs)

    def _parse_lines(self, top=False):
        """Parse newline-separated expressions at the current depth (INDENT
        already consumed if nested). Handles line ownership."""
        exprs = []
        while True:
            while self.at("NEWLINE"):
                self.next()
            if self.at("EOF"):
                break
            if self.at("DEDENT"):
                self.next()  # this block's terminator — consumed exactly once
                break
            expr = self.parse_expr()
            # line ownership: deeper lines attach to the line's last unit
            owner = self._last_unit
            if self.at("NEWLINE") and self.peek(1).type == "INDENT":
                self.next()
                self.next()
                if owner is None:
                    t = self.peek()
                    raise ParseError("indented lines need a call head to own them", (t.line, t.col))
                sub = []
                while not self.at("DEDENT") and not self.at("EOF"):
                    while self.at("NEWLINE"):
                        self.next()
                    if self.at("DEDENT") or self.at("EOF"):
                        break
                    sub.append(self.parse_expr())
                if self.at("DEDENT"):
                    self.next()
                new = Call(head=owner, args=sub, pos=owner.pos)
                expr = _replace(expr, owner, new)
            exprs.append(expr)
            if self._line_broken:
                self._line_broken = False  # the block consumed the line end
                continue
            if self.at("NEWLINE"):
                self.next()
            elif not (self.at("EOF") or self.at("DEDENT")):
                self.err("expected end of line")
        return exprs

    # --- expressions ---
    def parse_expr(self, greedy=True):
        e = self.parse_infix(greedy=greedy)
        if self.at("PUNCT", ",") and self.peek().glued:
            items = [e]
            while self.at("PUNCT", ",") and self.peek().glued:
                self.next()
                items.append(self.parse_infix(greedy=greedy))
            return Tup(items=items, pos=e.pos)
        return e

    def parse_infix(self, min_bp=0, greedy=True):
        left = self.parse_unit(greedy=greedy)
        while True:
            t = self.peek()
            if t.type == "OP" and t.glued and t.value in INFIX_BP:
                bp = INFIX_BP[t.value]
                if bp < min_bp:
                    break
                if t.value in CMP_OPS:
                    ops, rest = [], []
                    while self.peek().type == "OP" and self.peek().value in CMP_OPS and self.peek().glued:
                        ops.append(self.next().value)
                        rest.append(self.parse_infix(bp + 1, greedy=True))
                    left = Cmp(first=left, ops=ops, rest=rest, pos=(t.line, t.col))
                    continue
                self.next()
                right = self.parse_infix(bp + 1 if t.value != "**" else bp, greedy=True)
                left = Infix(op=t.value, left=left, right=right, pos=(t.line, t.col))
            else:
                break
        return left

    def parse_unit(self, greedy=True):
        """primary + postfix (+ sibling args when greedy). An argument's first
        unit is parsed with greedy=False so sibling args belong to the head."""
        e = self._postfix_primary()
        if greedy:
            args, kwargs = [], []
            zero_call = False
            # literals never act as call heads — their following units belong
            # to the enclosing call (`if n<= 1 (: a) (: b)` stays if(n<=1, a, b))
            while self._starts_arg() and not isinstance(e, Lit) and not self._line_broken:
                t = self.peek()
                if t.type == "PUNCT" and t.value == "(" and self.peek(1).type == "PUNCT" and self.peek(1).value == ")":
                    self.next()
                    self.next()
                    zero_call = True  # `f ()` — the bare-call marker
                    continue
                if t.type == "NAME" and self.peek(1).type == "OP" and self.peek(1).value == ":=" and self.peek(1).glued:
                    self.next()
                    self.next()
                    kwargs.append((t.value, self.parse_expr()))
                    continue
                args.append(self.parse_arg())
            if args or kwargs or zero_call:
                e = Call(head=e, args=args, kwargs=kwargs, pos=e.pos)
        return e

    def parse_arg(self):
        return self.parse_expr(greedy=False)

    def _starts_arg(self):
        t = self.peek()
        if t.type in ARG_STARTERS:
            return True
        if t.type == "PUNCT" and t.value in ("(", "[", ":"):
            return True
        return False

    def _postfix_primary(self):
        e = self._primary()
        while True:
            t = self.peek()
            if t.type == "OP" and t.value == "." and t.glued:
                self.next()
                name = self.eat("NAME")
                if name is None:
                    self.err("expected attribute name after '.'")
                e = Attr(obj=e, name=name.value, pos=(t.line, t.col))
            elif t.type == "PUNCT" and t.value == "[" and t.glued:
                self.next()
                idx = self.parse_expr()
                if not self.eat("PUNCT", "]"):
                    self.err("expected ']'")
                e = Sub(obj=e, index=idx, pos=(t.line, t.col))
            else:
                break
        self._last_unit = e
        # assignment as operand (walrus / statement): glued '=' after Name/Attr/Sub
        t = self.peek()
        if t.type == "OP" and t.value == "=" and t.glued:
            if isinstance(e, (Name, Attr, Sub)):
                self.next()
                value = self.parse_expr(greedy=True)
                e = Assign(target=e, value=value, pos=(t.line, t.col))
            elif _is_name_call(e):
                self.next()
                value = self.parse_expr(greedy=True)
                names = [e.head] + list(e.args)
                e = Assign(target=Tup(items=names, pos=e.pos), value=value, pos=(t.line, t.col))
            else:
                self.err("invalid assignment target")
        return e

    def _primary(self):
        t = self.peek()
        if t.type == "NUM":
            self.next()
            return Lit(value=t.value, pos=(t.line, t.col))
        if t.type == "STR":
            self.next()
            return Lit(value=t.value, pos=(t.line, t.col))
        if t.type == "FSTR":
            self.next()
            return FStr(raw=t.value, pos=(t.line, t.col))
        if t.type == "NAME":
            self.next()
            nxt = self.peek()
            if nxt.type == "PUNCT" and nxt.value == ":" and nxt.glued:
                self.next()
                return self._finish_lambda([Param(name=t.value)], (t.line, t.col))
            return Name(id=t.value, pos=(t.line, t.col))
        if t.type == "PUNCT" and t.value == ":":
            self.next()
            return self._finish_lambda([], (t.line, t.col))
        if t.type == "PUNCT" and t.value == "(":
            return self._paren_group()
        if t.type == "PUNCT" and t.value == "[":
            self.next()
            items = []
            while not self.at("PUNCT", "]"):
                if self.at("EOF") or self.at("NEWLINE"):
                    self.err("unterminated list literal")
                items.append(self.parse_expr(greedy=False))
            self.next()
            return ListLit(items=items, pos=(t.line, t.col))
        self.err(f"unexpected token {t.value!r}")

    def _paren_group(self):
        t = self.next()  # '('
        if self._is_param_group_after_open():
            params = self._parse_params()
            if not self.eat("PUNCT", ")"):
                self.err("expected ')' after parameter list")
            colon = self.eat("PUNCT", ":")
            if colon is None:
                self.err("expected ':' after parameter group")
            return self._finish_lambda(params, (t.line, t.col))
        inner = self.parse_expr()
        if not self.eat("PUNCT", ")"):
            self.err("expected ')'")
        self._line_broken = False
        return inner

    def _is_param_group_after_open(self):
        """'(' already consumed: scan to the matching ')' and check for a glued ':' after it."""
        depth = 1
        k = 0
        while True:
            t = self.peek(k)
            if t.type == "EOF":
                return False
            if t.type == "PUNCT" and t.value == "(":
                depth += 1
            elif t.type == "PUNCT" and t.value == ")":
                depth -= 1
                if depth == 0:
                    nxt = self.peek(k + 1)
                    return nxt.type == "PUNCT" and nxt.value == ":" and nxt.glued
            k += 1

    def _is_param_group(self):
        """Lookahead: '(' … matching ')' immediately followed by glued ':'."""
        depth = 0
        k = 0
        while True:
            t = self.peek(k)
            if t.type == "EOF":
                return False
            if t.type == "PUNCT" and t.value == "(":
                depth += 1
            elif t.type == "PUNCT" and t.value == ")":
                depth -= 1
                if depth == 0:
                    nxt = self.peek(k + 1)
                    return nxt.type == "PUNCT" and nxt.value == ":" and nxt.glued
            k += 1

    def _parse_params(self):
        params = []
        ret_ann = None
        while not self.at("PUNCT", ")"):
            t = self.peek()
            if t.type == "PUNCT" and t.value == ":":
                self.next()
                ret_ann = self._type_expr()
                break
            if t.type == "PUNCT" and t.value in ("..", "..."):
                self.next()
                p = Param(name=t.value, star=t.value == "..", dstar=t.value == "...")
                if self.at("PUNCT", ":") and self.peek().glued:
                    self.next()
                    p.ann = self._type_expr()
                params.append(p)
                continue
            if t.type != "NAME":
                self.err("expected parameter name")
            self.next()
            p = Param(name=t.value)
            if self.at("PUNCT", ":") and self.peek().glued:
                self.next()
                p.ann = self._type_expr()
            if self.at("OP", "=") and self.peek().glued:
                self.next()
                p.default = self.parse_unit(greedy=False)
            params.append(p)
        if ret_ann is not None:
            params.append(Param(name=":ret", ann=ret_ann))
        return params

    def _type_expr(self):
        """Annotation: a dotted name chain — never an assignment target."""
        t = self.eat("NAME")
        if t is None:
            self.err("expected annotation name")
        e = Name(id=t.value, pos=(t.line, t.col))
        while self.at("OP", ".") and self.peek().glued:
            self.next()
            name = self.eat("NAME")
            if name is None:
                self.err("expected attribute name after '.'")
            e = Attr(obj=e, name=name.value, pos=(t.line, t.col))
        return e

    def _finish_lambda(self, params, pos):
        if self.at("NEWLINE") and self.peek(1).type == "INDENT":
            self.next()
            self.next()
            exprs = self._parse_lines()
            self._line_broken = True  # the block ended the enclosing line
            body = Block(exprs=exprs, pos=pos)
        else:
            body = self.parse_expr()
        return Lambda(params=params, body=body, pos=pos)


def _is_name_call(e):
    return isinstance(e, Call) and isinstance(e.head, Name) and all(isinstance(a, Name) for a in e.args)


def _replace(tree, old, new):
    """Identity-based tree replacement of `old` with `new`."""
    if tree is old:
        return new
    from dataclasses import fields, is_dataclass

    if is_dataclass(tree):
        for f in fields(tree):
            v = getattr(tree, f.name)
            setattr(tree, f.name, _replace_value(v, old, new))
    return tree


def _replace_value(v, old, new):
    from dataclasses import is_dataclass

    if is_dataclass(v):
        return _replace(v, old, new)
    if isinstance(v, list):
        return [_replace_value(x, old, new) for x in v]
    if isinstance(v, tuple):
        return tuple(_replace_value(x, old, new) for x in v)
    return v


def parse(source):
    return Parser(lex(source)).parse_program()
