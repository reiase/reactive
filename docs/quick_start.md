![logo](assets/hlogo.svg)

`Reactive` 是一个Python下的响应式编程框架，目标是将响应式编程的一些思路引入到Python的数据与AI生态中：

- 声明式编程范式：让开发者更关注想要做什么（What）而不是怎么去做（How）；
- 回弹性（Resilient）：异常与失败不影响系统的可用性，而是得到遏制与隔离；
- 弹性与即使响应（Elastic&Responsive）：系统总是及时给出响应，即便在不断变化的负载下也能通过增加或者减少资源来保持高效处理速率；

`Reactive` 提供对Python中`list`与`iterator`的统一抽象`DataCollection`, 在向数据科学家和机器学习工程师提供高阶能力的同时尽量保持简洁易懂。`Reactive`可以通过`pip`命令快速安装：

```bash
pip install reactive-python
```

DataCollection
==============

不同于Java和C#等类C语言，Python天生就支持函数式编程范式。
然而在实际代码中却极少见到函数式编程的大量应用，我们猜测与Python的`map`与`filter`实现有关：
```python
map(lambda x: x+1, [1, 2, 3, 4])
map(lambda x: x+1, map(lambda y: y*2, [1, 2, 3, 4]))
```
如上述例子所示，嵌套调用的`map`很难让代码清晰易懂。
`DataCollection` 是`Reactive`提供的对`list`和`iterator`等Python核心数据结构的抽象，提供类似Jave和Scala等语言中的链式调用：

```python
import reactive as rv

(
  rv.of([1,2,3,4])
    .map(lambda x: x+1)
    .map(lambda y: y*2)
)
```

DataCollection支持常见的Reactive编程API（也称函数式编程API），比如：

- 变换操作：
  - `map(fn)`
  - `flatMap(fn)`
  - `filter(fn)`
- 聚合操作：
  - `batch(batch_size)`: 将数据按`batch_size`聚合一个个batch；
  - `flatten()`：将batch展开成；
  - `rolling(window_size)`：将数据按`window_size`去滑动窗口；
- 订阅操作：
  - `to_list()/collect()`：将处理后的数据按顺序收集为一个list对象；
  - `run()`：执行全部数据处理操作，但不回收结果；
  - `subscribe(fn)`：同上，但将结果交给`fn`处理；

流式计算与批量计算
---------------

我们可以从`list`或者`iterator`创建`DataCollection`对象。不过，从`list`创建的`DataCollection`表现更像一个普通的`list`:

1. `map()`操作总是立即执行
```python
>>> rv.of([1,2,3,4]).map(lambda x: x+1)
[2, 3, 4, 5]
```

2. 支持`list`相关操作

```python
>>> dc = rv.of([1,2,3,4])
>>> dc
[1, 2, 3, 4]

>>> dc[0]
1

>>> dc.append(5)
[1, 2, 3, 4, 5]
```

我们称这种`DataCollection`上的计算为批量计算。批量计算模式可以认为是对Python的`list`类型的简单增强。

从`iterator`创建的`DataCollection`表现更像一个`iterator`:

1. `map()`操作不会立即执行，而是在数据被消费时才执行

```python
>>> dc = rv.of(iter([1,2,3,4]))
>>> dc.map(lambda x: x+1)
<iterator of list> # 此处并未发生任何计算

>>> dc.collect()
[2, 3, 4, 5]
```

2. 执行时按每个元素逐个执行，比如：

```python
>>> dc.map(fnA).map(fnB)
fnA(1), fnB(1), fnA(2), fnB(2), fnA(3), fnB(3), fnA(4), fnB(4)
```

上述计算称为流式计算。流式计算模式可以认为是对Python的`iterator`类型的增强，稍后会介绍流式计算的一些高阶用法。

批量计算与流式计算可以通过`stream()`与`unstream()`进行切换：

- `stream()`：将`DataCollection`切换到流计算模式，已经为流模式则不做处理；
- `unstream()`：将`DataCollection`切换到批量计算模式，已经为批量计算模式则不做处理；

显式语义(explicit operation)与隐式语义(implicit operation)
-----------------------------------

借助`DataCollection`这个数据类型，`Reactive`为Python引入了简洁明了的链式调用语法以及流式计算能力。
但实际编程中，使用最为广泛的是`map()`操作，而频繁调用`map()`在语法上显得较为冗余。

此处介绍一种隐式调用语义，可以让语法更为简单明了：
```python
>>> def add_1(x): return x+1
>>> def mul_2(x): return x*2
>>> dc.map(add_1).map(mul_2)
```
可以简单写为：
```python
(
  dc.add_1()
    .mul_2()
)
```

表格数据
-------

`DataCollection`提供Pandas表格数据的一种便捷处理方式，比如:

```python
>>> import pandas as pd
>>> df = pd.DataFrame({"a": range(5)})
   a 
0  0
1  1
2  2
3  3
4  4
```

Pandas的`DataFrame`可以直接包装为DataCollection，并通过函数式接口处理指定列.

```python
>>> dc = rv.from_pandas(df)

>>> (
...   dc.add1["a", "b"]()
... 		.mul2["b", "c"]()
... )
   a  b   c
0  0  1   2
1  1  2   4
2  2  3   6
3  3  4   8
4  4  5  10

```

其中 `add1["a", "b"]` 表示以列`a` 为输入计算`add1`并将结果存入`b`. 

错误处理
-------

虽然链式调用和流式计算能够给数据处理带来很多便捷，但现实世界的数据总是充满了噪声，导致数据处理不得不面对处理失败的情况。`DataCollection`提供一种便捷的错误处理方式：

```python
>>> dc.safe().add_1().mul_2()
[Some(4), Some(6), Some(8), Some(10)]

>>> dc.safe().map(lambda x: 10/int(x-1))
[Empty(), Some(10.0), Some(5.0), Some(3.33)]
```

当启用`exception_safe`模式时，`Reactive`会自动替用户忽略相关错误，并将错误结果存入到`Empty`对象中，讲正确结果存入`Some`对象中。在数据处理结束后，可以通过`drop_empty()`或者`fill_empty()`两种策略进行错误处理：

```python
>>> dc.safe().map(lambda x: 10/int(x-1)).drop_empty()
[10.0, 5.0, 3.33]

>>> dc.safe().map(lambda x: 10/int(x-1)).fill_empty(None)
[None, 10.0, 5.0, 3.3333333333333335]
```

高阶特性介绍（TODO）
==========

1. 并行计算
2. 分布式计算
3. 编译优化

-------------------------------------------------------

### 特性

- 链式调用，可方便构建数据处理管线;
- 流式计算，可处理超大数据集而不受内存限制;
- 表格数据，方便按字段处理数据;
- 超参支持，支持MLOps功能;

### 用例

- 构建机器学习应用原型，并可以追踪试验配置和模型指标;
- 快速调优ML Pipeline性能;
- 部署ML Pipeline到生产环境，并优化性能;

快速开始
-------

### 安装

```bash
pip install reactive-python
```
### `DataCollection` 与Python列表

`DataCollection` 是对Python `list` 数据类型的直接增强. 可以比较便捷的从`list`创建`DataCollection`:

```python
>>> import reactive as rv
>>> dc = rv.new([0, 1, 2, 3])
>>> dc
[0, 1, 2, 3]

```

`DataCollection` 的行为基本与Python `list` 类型一致，可直接替代:

``` python
>>> dc = rv.of([0, 1, 2, 3])
>>> dc
[0, 1, 2, 3]

# indexing
>>> dc[1], dc[2]
(1, 2)

# slicing
>>> dc[:2]
[0, 1]

# appending
>>> dc.append(4).append(5)
[0, 1, 2, 3, 4, 5]

```

### 函数式编程接口与链式调用

`DataCollection` 提供诸如 `map` 和 `filter` 这种高阶函数:

```python
>>> rv.of([0, 1, 2, 3, 4]).map(lambda x: x*2)
[0, 2, 4, 6, 8]

>>> rv.of([0, 1, 2, 3, 4]).filter(lambda x: int(x%2)==0)
[0, 2, 4]

```

`map` 和 `filter` 也返回`DataCollection`类型, 因此我们在Python中也获得了链式调用的能力:

```python
>>> (
...   	rv.of([0, 1, 2, 3, 4])
...          .filter(lambda x: x%2==1)
...          .map(lambda x: x+1)
...          .map(lambda x: x*2)
... )
[4, 8]

```

### 扩展性

我们可以通过定义函数或者导入函数的形式来扩展 `DataCollection`， 比如:

```python
>>> def add1(x):
...   return x + 1
>>> (
...		rv.of([0, 1, 2, 3, 4])
... 		   .add1()
... )
[1, 2, 3, 4, 5]

```

`add1` 是定义在当前上下文的函数，我们可以将这种函数当做`DataCollection` 的API来调用而无需额外工作.

### 表格数据处理

`DataCollection`提供Pandas表格数据的一种便捷处理方式，比如:

```python
>>> import pandas as pd
>>> df = pd.DataFrame({"a": range(5)})

```

Pandas的`DataFrame`可以直接包装为DataCollection，并通过函数式接口处理指定列.

```python
>>> dc = reactive.from_pandas(df)

>>> def add1(x): return x+1
>>> def mul2(x): return x*2
>>> (
...   dc.add1["a", "b"]()
... 		.mul2["b", "c"]()
... )
   a  b   c
0  0  1   2
1  1  2   4
2  2  3   6
3  3  4   8
4  4  5  10

```

其中 `add1["a", "b"]` 表示以列`a` 为输入计算`add1`并将结果存入`b`. 

## Roadmap

DataCollection 目标是提供一套类似`scala.collection`的数据接口，但尽可能保持pythonic。深度学习和Python已经根本性的改变了数据科学和相关从业者，因此基于Python为开发者提供更好的体验，提升python代码的可读性和性能十分必要。

  - [ ] Collection API;
    - [ ] stream and unstream execution; 
    - [x] `map` and `filter`;
    - [x] `flatten` and `fold`;
    - [x] `batch` and `rolling`;
  - [ ] Tabular API;
    - [x] SISO (single input and single output);
    - [x] MIMO (multiple input and multiple output);
    - [ ] GraphQL support;
    - [ ] `groupby` API;
    - [ ] `aggregate` API;
  - [ ] Execution Engine;
    - [x] async and parallel execution;
    - [ ] native execution engine with Rust;
    - [x] Arrow-based colmular storage;
  - [ ] JIT Compiler;
    - [ ] numba compiler support;
    - [ ] jit compile hook;