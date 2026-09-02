# expyssion grammar & semantics — full example set (rev 3, final)

Seed of the proof corpus (ticket 007). Applies all owner corrections through 2025-09-01.

## 001 — Control-flow messages & return

```
clip= x:
  if x<0 :return 0
  x
# x<0 → clip 返回 0：consumed if 体透明，return 飞到 assigned 的 clip

f= :
  ret= : a
    return b
    c
  ret ()      # ret 自己接住自己的 return → 返回 b；f 不被打断
  d           # f 的值是 d
```

## 002 — Generators & comprehensions（无包装器，消费即驱动）

```
gen= : yield 1
gen ()                    # ❌ 响亮报错：unhandled yield
list gen                  # [1] —— list 内部驱动 gen（handler 活跃）
for gen x: print x        # for 同样驱动：1

list (for (range 3) x: yield x*x)              # [0, 1, 4]
dict (for (zip ks vs) (k v): yield k, v)       # 字典推导：yield 元组键值对
evens= list (for (range 100) x: if x%2==0 :yield x)
```

## 003 — Assignment & lvalues

```
x= 3
a[0]= b
a.c= b
(a b)= 3, 4           # 元组解构：a=3, b=4
x= y= 3               # 链式（walrus）
count= count+ 1       # 无增强运算符
g= :
  total= 0
  for xs x: total= total+ x
  total               # 隐式返回最后一行
```

## 004 — Grammar

```
# 调用
a b c               # a(b, c)
a b
  c                 # a(b(c)) —— 缩进归最后一个 token
f (a b c)           # f(a(b, c)) —— 括号内一个实参
f (a) (b)           # f(a, b) —— 括号参数表归属最近的头
add= (x y): x+ y    # 双参 lambda

# 中缀：符号、胶住左操作数、固定元数
a& b| c             # (a&b)|c —— & 优先于 |
a& b | c            # ❌ | 前没有胶着物 → 语法错误
(a& b)| c           # 想改结合顺序就加括号
a and b             # ❌ 词中缀不存在
and a b             # and/or 前缀函数（急切）；短路写 and a (: b)
not done            # not 是普通函数
x+ f 3              # x + f(3) —— 中缀永不变参头；(x+ f) 3 才是调用和

# 后缀与括号二元性
a.b                 # 属性；a .b 非法
a.b c               # a.b(c) 方法调用
xs[1]               # 下标：xs.__getitem__(1)
a[b c]              # a[b(c)] —— 下标固定单实参；多索引用元组 a[b, c]
xs[slice 1 3]       # 切片 = slice 构造器
[a b]               # 列表字面量（空格分离 = 独立列表）
f [a b]             # f 收到列表 [a, b] 作为实参
xs [i]              # xs 被调用，实参是列表 [i] —— 与 xs[i] 不同！

# 元组
3, 4                # 元组（异构容器）；同构集合用列表
k, v                # yield k, v 喂 dict

# 参数注解与 kwargs
add= (a:int b:int :int): a+ b     # 末尾无名 :int = 返回类型
connect= (host:string port:int= 80): ...
connect "example.com"             # port 缺省 80
connect "example.com" port:= 8080 # := 高优先级，免括号
sum_all= (..:int):
  total= 0
  for .. x: total= total+ x
  total                 # .. vararg（元组）；... kwarg（dict）

# 负号
-1                  # 词法折叠为负字面量
neg x               # 表达式取负；或 0- x
- x                 # ❌ 分离的 - 不是运算符

# 其他
1+ 2*3              # 7
int a/b             # 整除：算术中缀优先于实参边界 → int(a/b)
: a b c             # lambda: a(b, c) —— 单行体 = 整行一个表达式
```

## 005 — Scoping & assignment walk

```
make_counter= :
  n= 0
  :
    n= n+ 1         # n 绑定在词法祖先 → 就地修改（自动闭包 cell）
    n
c= make_counter ()
c ()    # 1
c ()    # 2        —— 容器 hack 不再需要

f= : total= 0
  for xs x: total= total+ x
  total             # 循环体内赋值修改 f 的 total ✓
```

## 006 — Concurrency

```
g= generator (: for (range 100) x: yield x)
list g    # ✓ 同线程（list 驱动 g）
# 另一线程驱动 g → 干净报错（线程亲和）
```

## 007 — Litmus programs（验收三程序）

```
febonacci= n: if n<=1 (:n) (: febonacci n- 1 n- 2)
febonacci 10        # 55 —— 分支是callable，字面量分支要包 thunk

nums= generator (: for (range 100) x: yield x)
list (for nums x: if x%3==0 :yield x*x)     # [0, 9, 36, 81, ...]

guard= x:
  if x<0 :return 0
  x*2
```

## 010 — Protocol walk-through（normative as-if）

```
list (for (range 2) x: yield x)
# list 的 call loop：spawn for-call（实参求值在 handler 活跃下）
#   yield 0 → Yield(0) 冒泡 → list 消费、收集、Resume
#   yield 1 → 收集 → Resume → Done → list 返回 [0, 1]
```

clip 的两种编译形态：

```python
# as-if（规范语义）
def clip(x):
    try:
        _e.if_(x < 0, lambda: _e.raise_return(0), lambda: _e.null)
        return x
    except _e.Return as r:
        return r.value

# elided（编译器可直出的可读形态）
def clip(x):
    if x < 0:
        return 0
    return x
```

elision 机会（非 spec 承诺）：`list (for (range 2) x: yield x)` → `[x for x in range(2)]`。

## 011 — Close & resources（清理责任归驱动者）

```
g= generator (:
  with_resource (open "data.txt") (:fh:
    for fh line: yield line))
list g          # 驱动到完成 → finally 关文件
for g line: break
# break → for 的驱动循环注入 GeneratorExit → finally 关文件（驱动者拥有清理）
```

## 012 — Handler resolution（v1 内建白名单）

```
matrix= list (for (range 3) x: list (for (range 2) y: yield y))
# [[0, 1], [0, 1], [0, 1]] —— 内层 list 是最近 handler，yield 归它
# 外层 list 收到的是内层的返回值（非 yield）
# 无用户自定义 handler；tag 字段已为未来预留
```

## 013 — Elision

```
x+ y*2      # 未遮蔽纯内建 → 无同步点，直出 x + y*2
f x         # 普通 lambda → 保留同步点（f 可能 yield）
```

## 014 — Python interop

```
np= import numpy
a= np.arange 10       # np.arange(10)，C 段原子
a.max ()              # 9
sorted xs             # Python 内建经包装可用
xs 5                  # ❌ 原生 TypeError（list 不可调用——文档旧规则已废）
```

## 015 — Errors

```
(: return 3) ()            # ❌ return outside function
for (range 3) x: break     # ✓ 循环实现接住
break                      # ❌ break outside loop
```

## 016 — Library

```
if c t                 # else 缺省 → null
while (: x> 0) :
  print x
  x= x- 1
m= map (: x: x*2) xs   # 惰性
first (filter (: x: x%2==0) xs)
n= len xs
q= xs[slice 1 3]
r= int a/b          # 整除 = int(a/b)，无需 helper
neg x               # 表达式取负
```
