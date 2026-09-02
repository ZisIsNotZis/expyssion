import pytest

from expyssion.lexer import lex, ExpyssionSyntaxError as LexError


def toks(src):
    return [(t.type, t.value, t.glued) for t in lex(src)
            if t.type not in ("NEWLINE", "INDENT", "DEDENT", "EOF")]


def structure(src):
    return [(t.type, t.value) for t in lex(src)]


def test_call_siblings():
    assert toks("a b c") == [("NAME", "a", False), ("NAME", "b", False), ("NAME", "c", False)]


def test_glue_flag_on_infix():
    assert toks("a& b| c") == [
        ("NAME", "a", False), ("OP", "&", True),
        ("NAME", "b", False), ("OP", "|", True),
        ("NAME", "c", False),
    ]


def test_detached_operator_is_error():
    with pytest.raises(LexError):
        lex("a & b")


def test_detached_minus_never_operator():
    with pytest.raises(LexError):
        lex("a - b")


def test_negative_literal_folds():
    assert toks("-1") == [("NUM", -1, False)]
    assert toks("f x -1") == [("NAME", "f", False), ("NAME", "x", False), ("NUM", -1, False)]
    assert toks("x- 1") == [("NAME", "x", False), ("OP", "-", True), ("NUM", 1, False)]
    assert toks("0- x") == [("NUM", 0, False), ("OP", "-", True), ("NAME", "x", False)]


def test_multichar_ops():
    assert toks("a== b") == [("NAME", "a", False), ("OP", "==", True), ("NAME", "b", False)]
    assert toks("a** b") == [("NAME", "a", False), ("OP", "**", True), ("NAME", "b", False)]
    assert toks("a<= b") == [("NAME", "a", False), ("OP", "<=", True), ("NAME", "b", False)]


def test_kwargs_token():
    assert toks("port:= 8080") == [("NAME", "port", False), ("OP", ":=", True), ("NUM", 8080, False)]


def test_strings_and_fstrings():
    assert toks('"hi"') == [("STR", "hi", False)]
    assert toks("f\"x={x}\"") == [("FSTR", 'f"x={x}"', False)]
    assert toks("'it\\'s'") == [("STR", "it's", False)]


def test_numbers():
    assert toks("1.5 2e3") == [("NUM", 1.5, False), ("NUM", 2000.0, False)]


def test_names_dots():
    assert toks("a.b c") == [("NAME", "a", False), ("OP", ".", True), ("NAME", "b", True), ("NAME", "c", False)]
    got = toks("f= (.. ... :int)")
    assert got[-5:] == [("PUNCT", "..", True), ("PUNCT", "...", False), ("PUNCT", ":", False), ("NAME", "int", True), ("PUNCT", ")", True)]


def test_comments_and_blank_lines():
    assert toks("# only a comment\n\na b  # trailing\n") == [("NAME", "a", False), ("NAME", "b", False)]


def test_indent_dedent_structure():
    s = structure("a\n  b\n  c\nd\n")
    assert s == [
        ("NAME", "a"), ("NEWLINE", "\n"),
        ("INDENT", "  "), ("NAME", "b"), ("NEWLINE", "\n"),
        ("NAME", "c"), ("NEWLINE", "\n"),
        ("DEDENT", ""), ("NAME", "d"), ("NEWLINE", "\n"),
        ("EOF", ""),
    ]


def test_colon_and_equals_are_plain_tokens():
    assert toks("x= 3") == [("NAME", "x", False), ("OP", "=", True), ("NUM", 3, False)]
    assert toks(": a b") == [("PUNCT", ":", False), ("NAME", "a", False), ("NAME", "b", False)]
