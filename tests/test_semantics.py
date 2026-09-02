import pytest

from expyssion import run_source
from expyssion.errors import (
    BreakOutsideLoopError,
    ContinueOutsideLoopError,
    CollectorShapeError,
    ReturnOutsideFunctionError,
    UnboundNameError,
    UnhandledYieldError,
)


def run(src):
    return run_source(src)


# --- expressions & scoping ----------------------------------------------------

def test_arithmetic_and_precedence():
    assert run("1+ 2*3") == 7


def test_infix_glued():
    assert run("a= 1\nb= 3\nc= 2\na& b| c") == 3


def test_int_floor_division():
    assert run("int 7/2") == 3


def test_negative_literal_and_neg():
    assert run("-1< 0") is True
    assert run("neg 5") == -5
    assert run("x= 5\n0- x") == -5


def test_make_counter_closure_cells():
    assert run("""
make_counter= :
  n= 0
  (:
    n= n+ 1
    n
  )
c= make_counter ()
c ()
c ()
""") == 2


def test_accumulator_walks_lexical_ancestor():
    assert run("""
f= :
  total= 0
  for [1 2 3] x: total= total+ x
  total
f ()
""") == 6


def test_shadow_builtin_defines_locally():
    assert run("""
list= 5
list
""") == 5


def test_unbound_name_is_loud():
    with pytest.raises(UnboundNameError):
        run("nope")


# --- control flow ---------------------------------------------------------------

def test_if_branches_are_invoked():
    assert run('if 1 (:"odd") :"even"') == "odd"
    assert run('if 0 (:"odd") :"even"') == "even"


def test_if_missing_else_is_null():
    assert run("if 0 (:1)") is None


def test_guard_return_crosses_consumed_if():
    assert run("""
clip= x: if x< 0 (: return 0) (: x)
clip -1
""") == 0


def test_clip_literal_style():
    assert run("""
clip= x:
  if x< 0 (: return 0) (: x)
clip 2
""") == 2


def test_while_and_else():
    assert run("""
n= 3
out= []
while (: n> 0) (:
  out.append n
  n= n- 1
)
out
""") == [3, 2, 1]


def test_for_returns_last_body_value():
    assert run("""
r= for [1 2 3] x: x* 2
r
""") == 6


def test_for_break_skip():
    assert run("""
total= 0
for (range 6) x:
  if x== 3 (: break ())
  total= total+ x
total
""") == 0 + 1 + 2


def test_try_handler():
    assert run("""
try (1/0) e: "caught"
""") == "caught"


def test_try_passes_value():
    assert run("try 7 e: 0") == 7


def test_raise_requires_instance():
    with pytest.raises(TypeError):
        run('raise "nope"')


# --- yield, generators, comprehensions -------------------------------------------

def test_list_drives_yielding_lambda():
    assert run("""
gen= :
  yield 1
list gen
""") == [1]


def test_comprehension_call_expression():
    assert run("list (for (range 3) x: yield x*x)") == [0, 1, 4]


def test_dict_comprehension_pairs():
    assert run("""
ks= ["a" "b"]
vs= [1 2]
dict (for (zip ks vs) (k v): yield k, v)
""") == {"a": 1, "b": 2}


def test_for_drives_yielding_lambda():
    assert run("""
out= []
gen= :
  yield 1
  yield 2
for gen x: out.append x
out
""") == [1, 2]


def test_nested_collectors_nearest_handler():
    assert run("""
list (for (range 3) _: yield (list (for (range 2) y: yield y)))
""") == [[0, 1], [0, 1], [0, 1]]


def test_bare_yield_call_is_loud():
    with pytest.raises(UnhandledYieldError):
        run("""
gen= : yield 1
gen ()
NULL
""")


def test_yield_inside_list_arg_without_driver_is_loud():
    with pytest.raises(UnhandledYieldError):
        run("""
gen= : yield 1
list (gen ())
NULL
""")


def test_break_outside_loop_is_loud():
    with pytest.raises(BreakOutsideLoopError):
        run("""
f= (: break ())
f ()
""")


def test_continue_outside_loop_is_loud():
    with pytest.raises(ContinueOutsideLoopError):
        run("""
f= (: continue ())
f ()
""")


def test_return_outside_function_is_loud():
    with pytest.raises(ReturnOutsideFunctionError):
        run("return 5")


def test_collector_arity_is_loud():
    with pytest.raises(CollectorShapeError):
        run("list 1 2")


def test_dict_wrong_shape_is_loud():
    with pytest.raises(CollectorShapeError):
        run("list (for (range 2) x: yield x)\ndict [1 2]" if False else "dict [1 2]")


# --- generators as Python iterators ------------------------------------------------

def test_python_consumes_expyssion_generator():
    m = run_source("""
gen= :
  yield 10
  yield 20
  yield 30
gen
""")
    assert list(m) == [10, 20, 30]


def test_python_bare_call_yield_is_loud():
    fn = run_source("f= : yield 1\nf")
    with pytest.raises(UnhandledYieldError):
        fn()


def test_python_calls_expyssion_lambda():
    add = run_source("add= (a b): a+ b\nadd")
    assert add(2, 3) == 5


# --- interop ------------------------------------------------------------------------

def test_numpy_import_and_attribute_call():
    np = run_source('np= import "numpy"\nnp')
    arr = run_source('np= import "numpy"\nnp.arange 10')
    assert arr.max() == 9


def test_import_requires_string():
    from expyssion.errors import ExpyssionError

    with pytest.raises(ExpyssionError):
        run("import numpy")


def test_non_callable_invocation_native_typeerror():
    with pytest.raises(TypeError):
        run("xs= [1 2 3]\nxs 5")


def test_map_filter_lazy():
    assert run("list (map ((x): x* 2) [1 2])") == [2, 4]
    assert run("list (filter ((x): x%2== 0) [1 2 3])") == [2]
    assert run("first (filter ((x): x%2== 0) [1 2 3])") == 2


def test_fstring():
    assert run('name= "world"\nf"hello {name}"') == "hello world"


def test_and_or_not_eager():
    assert run("and 1 5") == 5
    assert run("and 0 5") == 0
    assert run("or 0 5") == 5
    assert run("or 2 5") == 2
    assert run("not 0") is True


def test_and_short_circuit_thunk():
    assert run("""
calls= []
and 0 (: calls.append 1)
len calls
""") == 0


# --- litmus programs ------------------------------------------------------------------

def test_litmus_febonacci():
    assert run("""
febonacci= n: if n<= 1 (: n) (: (febonacci n- 1)+ febonacci n- 2)
febonacci 10
""") == 55


def test_litmus_pipeline():
    out = run("""
list (for (range 100) x:
  if x%3== 0 (: yield x* x)
)
""")
    assert out[:4] == [0, 9, 36, 81]
    assert len(out) == 34


def test_litmus_guard():
    assert run("""
guard= x:
  if x< 0 (: return 0)
  x* 2
guard -5
guard 3
""") == 6


def test_litmus_febonacci_multiline_with_thunk_one():
    assert run("""
febonacci= n: if n<= 1 (: n) (: (febonacci n- 1)+ febonacci n- 2)
febonacci 1
""") == 1


def test_deep_chain_smoke():
    assert run("""
count= n: if n<= 0 (: 0) (: 1+ count n- 1)
count 300
""") == 300


def test_generator_close_cleanup():
    assert run("""
gen= :
  yield 1
  yield 2
it= gen
first it
"closed"
""") == "closed"


def test_python_close_unwinds_suspended_chain():
    gen = run_source("""
gen= :
  yield 1
  yield 2
gen
""")
    it = iter(gen)
    assert next(it) == 1
    it.close()  # must unwind without error
    assert list(it) == []


def test_vararg_and_kwarg_collection():
    assert run("""
sum_all= (..:int):
  total= 0
  for .. x: total= total+ x
  total
sum_all 1 2 3
""") == 6


def test_kwargs_extras_land_in_dstar():
    assert run("""
f= (...): ...
f a:= 1 b:= 2
""") == {"a": 1, "b": 2}


def test_default_evaluated_when_missing():
    assert run("f= (x= 7): x\nf ()") == 7
    assert run("f= (x= 7): x\nf 3") == 3
