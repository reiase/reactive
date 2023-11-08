DataCollection
==============

DataCollection is an extended data structure for data science and machine learning tasks. It is designed to support advanced features but kept as simple as Python list or iterable. 

DataCollection is an experimental fork of `towhee.DataCollection` with effects that having better MLOps support. 

### Features

- Method-chaining API that makes building data processing pipeline much easier;
- Streaming computation that allows large-scale data beyond the memory limitation;
- Easier tabular data programming API;
- Hyper-parameter support in data processing;

### Use Cases


- Building prototyping ML pipeline with experiment config and metric tracking;
- Tuning ML pipeline performance with ease;
- Deploying ML application into production;

Quick Start
------------

### Installation

```bash
pip install hyperdata
```
### DataCollection as a Python List

`DataCollection` is an enhancement to the `list` data type in Python. Creating a DataCollection from a list is as simple as:

```python
>>> import hyperdata
>>> dc = hyperdata.new([0, 1, 2, 3])
>>> dc
[0, 1, 2, 3]

```

The behavior of DataCollection is designed to be a drop-in-place replacement for the Python `list`:

``` python
>>> dc = hyperdata.new([0, 1, 2, 3])
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

### Functional API and Method-Chaining Style

DataCollection provides high-order functions such as `map` and `filter`:

```python
>>> hyperdata.new([0, 1, 2, 3, 4]).map(lambda x: x*2)
[0, 2, 4, 6, 8]

>>> hyperdata.new([0, 1, 2, 3, 4]).filter(lambda x: int(x%2)==0)
[0, 2, 4]

```

The `map` and `filter` always return a new DataCollection, making the method-chaining style possible in python:

```python
>>> (
...   	hyperdata.new([0, 1, 2, 3, 4])
...          .filter(lambda x: x%2==1)
...          .map(lambda x: x+1)
...          .map(lambda x: x*2)
... )
[4, 8]

```

### Extendable

DataCollection is designed to be extendable by simply defining or import functions:

```python
>>> def add1(x):
...   return x + 1
>>> (
...		hyperdata.new([0, 1, 2, 3, 4])
... 		   .add1()
... )
[1, 2, 3, 4, 5]

```

we can directly call the function `add1` defined in the context as an API of DataCollection.

### Tabular Data Processing

DataCollection provides an easier way for processing tabular data in Pandas, for example:

```python
>>> import pandas as pd
>>> df = pd.DataFrame({"a": range(5)})

```

The DataFrame can be wrapped into a DataCollection, and apply function to different columns.

```python
>>> dc = hyperdata.from_pandas(df)

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

where `add1["a", "b"]` means that we apply `add1` to column `a` and store the output into column `b`. 

## Roadmap

DataCollection aims to provide a collection API similar to `scala.collection`, but try to be more pythonic. Deep learning and Python have fundamentally changed data science and players in the area. And DataCollection tries to improve the readability and performance of ML-related python codes.


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