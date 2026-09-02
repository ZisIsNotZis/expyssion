import pytest

from expyssion.errors import ExpyssionSyntaxError
from expyssion.parser import parse
from expyssion.nodes import Assign, Attr, Block, Call, Cmp, FStr, Infix, Lambda, ListLit, Lit, Name, Sub, Tup


def one(src):
    b = parse(src)
    assert isinstance(b, Block) and len(b.exprs) == 1
    return b.exprs[0]


def test_call_siblings():
    e = one("a b c")
    assert isinstance(e, Call) and e.head == Name(id="a") and len(e.args) == 2


def test_indent_ownership_last_token():
    e = parse("a b\n  c\n").exprs[0]
    inner = e.args[0]
    assert isinstance(inner, Call) and inner.head == Name(id="b") and len(inner.args) == 1


def test_indent_ownership_no_args():
    e = parse("a\n  b\n  c\n").exprs[0]
    assert isinstance(e, Call) and e.head == Name(id="a") and len(e.args) == 2


def test_paren_arglist_nearest_head():
    e = one("f (a) (b)")
    assert isinstance(e, Call) and len(e.args) == 2


def test_paren_group_is_one_expression():
    e = one("f (a b c)")
    arg = e.args[0]
    assert isinstance(arg, Call) and arg.head == Name(id="a") and len(arg.args) == 2


def test_group_call_result():
    e = one("(make_adder 3) 5")
    assert isinstance(e, Call) and isinstance(e.head, Call)


def test_infix_precedence():
    e = one("1+ 2*3")
    assert isinstance(e, Infix) and e.op == "+" and isinstance(e.right, Infix) and e.right.op == "*"


def test_infix_never_variadic_head():
    e = one("x+ f 3")
    assert isinstance(e, Infix) and isinstance(e.right, Call) and e.right.head == Name(id="f")


def test_infix_binds_tighter_than_arg_boundary():
    e = one("int a/b")
    assert isinstance(e, Call) and isinstance(e.args[0], Infix) and e.args[0].op == "/"


def test_comparison_chain():
    e = one("a< b< c")
    assert isinstance(e, Cmp) and e.ops == ["<", "<"] and len(e.rest) == 2


def test_detached_op_is_parse_error():
    with pytest.raises(ExpyssionSyntaxError):
        parse("a & b\n")


def test_subscript_single_index():
    e = one("a[b c]")
    assert isinstance(e, Sub) and isinstance(e.index, Call)


def test_list_literal():
    e = one("f [a b]")
    assert isinstance(e, Call) and isinstance(e.args[0], ListLit) and len(e.args[0].items) == 2


def test_attribute_call():
    e = one("a.b c")
    assert isinstance(e, Call) and isinstance(e.head, Attr) and e.head.name == "b"


def test_tuple_and_destructure():
    e = one("(a b)= 3, 4")
    assert isinstance(e, Assign) and isinstance(e.target, Tup) and len(e.target.items) == 2
    assert isinstance(e.value, Tup)


def test_chained_walrus():
    e = one("x= y= 3")
    assert isinstance(e, Assign) and isinstance(e.value, Assign)


def test_subscript_assign():
    e = one("a[0]= b")
    assert isinstance(e, Assign) and isinstance(e.target, Sub)


def test_walrus_in_arg_position():
    e = one("f x= 3")
    assert isinstance(e, Call) and isinstance(e.args[0], Assign)


def test_lambda_zero_params_inline():
    e = one(": a b c")
    assert isinstance(e, Lambda) and e.params == [] and isinstance(e.body, Call)


def test_lambda_bare_single_param():
    e = one("f= x: x+ 1")
    lam = e.value
    assert isinstance(lam, Lambda) and len(lam.params) == 1 and lam.params[0].name == "x"


def test_lambda_param_group_full():
    e = one("add= (a:int b:int= 2 .. ... :int): a")
    lam = e.value
    ps = lam.params
    assert [p.name for p in ps[:4]] == ["a", "b", "..", "..."]
    assert ps[0].ann.id == "int" and ps[1].default.value == 2
    assert ps[4].name == ":ret" and ps[4].ann.id == "int"


def test_lambda_block_body():
    lam = parse("f= x:\n  x+ 1\n  x* 2\n").exprs[0].value
    assert isinstance(lam.body, Block) and len(lam.body.exprs) == 2


def test_kwargs_call_site():
    e = one('connect "example.com" port:= 8080')
    assert e.kwargs == [] or len(e.kwargs) == 1
    assert e.kwargs[0][0] == "port"


def test_negative_literal_and_literals():
    e = one("f x -1")
    assert e.args[1].value == -1
    e = one('"hi"')
    assert e.value == "hi"
    e = one('f"x={x}"')
    assert isinstance(e, FStr)


def test_collector_comprehension_shapes():
    e = one("list (for (range 3) x: yield x*x)")
    assert isinstance(e, Call) and e.head == Name(id="list")
    arg = e.args[0]
    assert isinstance(arg, Call) and arg.head == Name(id="for") and len(arg.args) == 2


def test_slice_via_constructor():
    e = one("xs[slice 1 3]")
    assert isinstance(e, Sub) and isinstance(e.index, Call) and e.index.head == Name(id="slice")


def test_comments_ignored():
    e = one("a b # trailing\n")
    assert isinstance(e, Call) and len(e.args) == 1
