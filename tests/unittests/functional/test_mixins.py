# Copyright 2021 Zilliz. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import doctest
import unittest
from pathlib import Path

import reactive
import reactive.mixins.computer_vision
import reactive.mixins.config
import reactive.mixins.data_processing
import reactive.mixins.dataframe
import reactive.mixins.dataset
import reactive.mixins.list
import reactive.mixins.metric
import reactive.mixins.parallel
import reactive.mixins.safe
import reactive.mixins.serve
import reactive.mixins.state
import reactive.mixins.stream
import numpy as np
from reactive import dc

public_path = Path(__file__).parent.parent.resolve()


def load_tests(loader, tests, ignore):
    # pylint: disable=unused-argument
    for mod in [
        reactive.mixins.computer_vision,
        reactive.mixins.dataset,
        reactive.mixins.dataframe,
        reactive.mixins.metric,
        reactive.mixins.parallel,
        reactive.mixins.state,
        reactive.mixins.serve,
        reactive.mixins.column,
        reactive.mixins.config,
        reactive.mixins.list,
        reactive.mixins.data_processing,
        reactive.mixins.stream,
        reactive.mixins.safe,
    ]:
        tests.addTests(doctest.DocTestSuite(mod))

    return tests


# pylint: disable=import-outside-toplevel


class TestMetricMixin(unittest.TestCase):
    """
    Unittest for MetricMixin.
    """

    def test_hit_ratio(self):
        true = [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]
        pred_1 = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]
        pred_2 = [[0, 1, 2, 3, 4, 5, 6, 7, 8]]
        pred_3 = [[0, 11, 12]]

        mhr = reactive.mixins.metric.mean_hit_ratio
        self.assertEqual(1, mhr(true, pred_1))
        self.assertEqual(0.8, mhr(true, pred_2))
        self.assertEqual(0, mhr(true, pred_3))

    def test_average_precision(self):
        true = [[1, 2, 3, 4, 5]]
        pred_1 = [[1, 6, 2, 7, 8, 3, 9, 10, 4, 5]]
        pred_2 = [[0, 1, 6, 7, 2, 8, 3, 9, 10]]
        pred_3 = [[0, 11, 12]]

        trues = [[1, 2, 3, 4, 5], [1, 2, 3, 4, 5]]
        pred_4 = [[1, 6, 2, 7, 8, 3, 9, 10, 4, 5], [0, 1, 6, 7, 2, 8, 3, 9, 10]]

        mean_ap = reactive.mixins.metric.mean_average_precision
        self.assertEqual(0.62, round(mean_ap(true, pred_1), 2))
        self.assertEqual(0.44, round(mean_ap(true, pred_2), 2))
        self.assertEqual(0, mean_ap(true, pred_3))
        self.assertEqual(0.53, round(mean_ap(trues, pred_4), 2))


class TestColumnComputing(unittest.TestCase):
    """
    Unit test for column-based computing.
    """

    def test_siso(self):
        df = dc["a"](range(10)).to_column().runas_op["a", "b"](func=lambda x: x + 1)

        self.assertTrue(all(map(lambda x: x.a == x.b - 1, df)))

    def test_simo(self):
        df = (
            dc["a"](range(10))
            .to_column()
            .runas_op["a", ("b", "c")](func=lambda x: (x + 1, x - 1))
        )

        self.assertTrue(all(map(lambda x: x.a == x.b - 1, df)))
        self.assertTrue(all(map(lambda x: x.a == x.c + 1, df)))

    def test_miso(self):
        df = (
            dc["a", "b"]([range(10), range(10)])
            .to_column()
            .runas_op[("a", "b"), "c"](func=lambda x, y: x + y)
        )

        self.assertTrue(all(map(lambda x: x.c == x.a + x.b, df)))

    def test_mimo(self):
        df = (
            dc["a", "b"]([range(10), range(10)])
            .to_column()
            .runas_op[("a", "b"), ("c", "d")](func=lambda x, y: (x + 1, y - 1))
        )

        self.assertTrue(all(map(lambda x: x.a == x.c - 1 and x.b == x.d + 1, df)))


class TestCompileMixin(unittest.TestCase):
    """
    Unittest for CompileMixin.
    """

    def test_compile(self):
        import time

        from reactive import register

        @register(name="inner_distance")
        def inner_distance(query, data):
            dists = []
            for vec in data:
                dist = 0
                for i in range(len(vec)):
                    dist += vec[i] * query[i]
                dists.append(dist)
            return dists

        data = [np.random.random((10000, 128)) for _ in range(10)]
        query = np.random.random(128)

        t1 = time.time()
        _ = (
            reactive.new["a"](data)
            .runas_op["a", "b"](func=lambda _: query)
            .inner_distance[("b", "a"), "c"]()
        )
        t2 = time.time()
        _ = (
            reactive.new["a"](data)
            .config(jit="numba")
            .runas_op["a", "b"](func=lambda _: query)
            .inner_distance[("b", "a"), "c"]()
        )
        t3 = time.time()
        # self.assertTrue(t3 - t2 < t2 - t1)

    def test_failed_compile(self):
        from reactive import register

        @register(name="inner_distance1")
        def inner_distance1(query, data):
            data = np.array(data)  # numba does not support np.array(data)
            dists = []
            for vec in data:
                dist = 0
                for i in range(len(vec)):
                    dist += vec[i] * query[i]
                dists.append(dist)
            return dists

        data = [np.random.random((10000, 128)) for _ in range(10)]
        query = np.random.random(128)

        (
            reactive.new["a"](data)
            .config(jit="numba")
            .runas_op["a", "b"](func=lambda _: query)
            .inner_distance1[("b", "a"), "c"]()
        )


if __name__ == "__main__":
    unittest.main()
