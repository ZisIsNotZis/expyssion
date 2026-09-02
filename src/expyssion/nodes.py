"""AST node types. Positions are (line, col) 1-indexed."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Node:
    pos: tuple | None = field(default=None, compare=False)


@dataclass
class Name(Node):
    id: str = ""


@dataclass
class Lit(Node):
    value: Any = None


@dataclass
class FStr(Node):
    raw: str = ""  # original token text, e.g. f"x={x}"


@dataclass
class ListLit(Node):
    items: list = field(default_factory=list)


@dataclass
class Tup(Node):
    items: list = field(default_factory=list)


@dataclass
class Attr(Node):
    obj: Any = None
    name: str = ""


@dataclass
class Sub(Node):
    obj: Any = None
    index: Any = None


@dataclass
class Infix(Node):
    op: str = ""
    left: Any = None
    right: Any = None


@dataclass
class Cmp(Node):
    first: Any = None
    ops: list = field(default_factory=list)
    rest: list = field(default_factory=list)


@dataclass
class Param:
    name: str = ""
    ann: Any = None  # expr or None (documentation-only)
    default: Any = None  # expr or None
    star: bool = False  # ..
    dstar: bool = False  # ...


@dataclass
class Lambda(Node):
    params: list = field(default_factory=list)  # [Param]
    body: Any = None  # expr or Block


@dataclass
class Block(Node):
    exprs: list = field(default_factory=list)


@dataclass
class Call(Node):
    head: Any = None
    args: list = field(default_factory=list)
    kwargs: list = field(default_factory=list)  # [(name, expr)]


@dataclass
class Assign(Node):
    target: Any = None  # Name | Attr | Sub | Tup(names)
    value: Any = None
