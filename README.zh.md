响应式Python编程
==============

`Reactive` 是一个Python下的响应式编程框架，目标是将响应式编程的一些思路引入到Python的数据与AI生态中：

- 声明式编程范式：让开发者更关注想要做什么（What）而不是怎么去做（How）；
- 回弹性（Resilient）：异常与失败不影响系统的可用性，而是得到遏制与隔离；
- 弹性与即使响应（Elastic&Responsive）：系统总是及时给出响应，即便在不断变化的负载下也能通过增加或者减少资源来保持高效处理速率；

`Reactive` 提供对Python中`list`与`iterator`的统一抽象`DataCollection`, 在向数据科学家和机器学习工程师提供高阶能力的同时尽量保持简洁易懂。 

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