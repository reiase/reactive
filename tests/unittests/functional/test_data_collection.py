import doctest
import unittest
from collections import namedtuple
from pathlib import Path

import reactive as rv
import reactive.datacollection
import reactive.types.option
from reactive import DataCollection, Entity, register

public_path = Path(__file__).parent.parent.resolve()


@register
def add_1(x):
    return x + 1


@register(name="add")
class MyAdd:
    def __init__(self, val):
        self.val = val

    def __call__(self, x):
        return x + self.val


@register(name="mul")
class MyMul:
    def __init__(self, val):
        self.val = val

    def __call__(self, x):
        return x * self.val


class TestDataCollection(unittest.TestCase):
    """
    tests for data collection
    """

    def test_example_for_basic_api(self):
        dc = rv.of(range(10))
        result = dc.map(lambda x: x + 1).filter(lambda x: x < 3)
        self.assertListEqual(list(result), [1, 2])

    def test_example_for_multiple_line_statement(self):
        dc = DataCollection(range(5))
        result = dc.add(val=1).mul(val=2).to_list()
        self.assertListEqual(result, [2, 4, 6, 8, 10])

    def test_runas_op(self):
        def add(x):
            return x + 1

        entities = [Entity(a=i, b=i + 1) for i in range(5)]
        dc = DataCollection(entities)

        res = dc.runas_op["a", "b"](func=lambda x: x - 1)
        for i in res:
            self.assertTrue(i.a == i.b + 1)

        res = dc.runas_op["a", "b"](func=add)
        for i in res:
            self.assertTrue(i.a == i.b - 1)

    def test_head(self):
        entities = [Entity(a=i, b=i + 1) for i in range(5)]
        dc = DataCollection(entities)

        dc.head(1)

    # def test_classifier_procedure(self):
    #     csv_path = public_path / 'test_util' / 'data.csv'
    #     out = DataCollection.read_csv(csv_path=csv_path).unstream()

    #     # pylint: disable=unnecessary-lambda
    #     out = (
    #         out.runas_op['a', 'a'](func=lambda x: int(x))
    #             .runas_op['b', 'b'](func=lambda x: int(x))
    #             .runas_op['c', 'c'](func=lambda x: int(x))
    #             .runas_op['d', 'd'](func=lambda x: int(x))
    #             .runas_op['e', 'e'](func=lambda x: int(x))
    #             .runas_op['target', 'target'](func=lambda x: int(x))
    #     )

    #     out = out.tensor_hstack[('a', 'b', 'c', 'd', 'e'), 'fea']()

    #     train, test = out.split_train_test()

    #     train.set_training().logistic_regression[('fea', 'target'), 'lr_train_predict'](name='logistic')

    #     test.set_evaluating(train.get_state()) \
    #         .logistic_regression[('fea', 'target'), 'lr_evaluate_predict'](name='logistic') \
    #         .with_metrics(['accuracy', 'recall']) \
    #         .evaluate['target', 'lr_evaluate_predict']('lr') \
    #         .report()

    #     train.set_training().decision_tree[('fea', 'target'), 'dt_train_predict'](name='decision_tree')

    #     test.set_evaluating(train.get_state()) \
    #         .decision_tree[('fea', 'target'), 'dt_evaluate_predict'](name='decision_tree') \
    #         .with_metrics(['accuracy', 'recall']) \
    #         .evaluate['target', 'dt_evaluate_predict']('dt') \
    #         .report()

    # train.set_training().svc[('fea', 'target'), 'svm_train_predict'](name='svm_classifier')

    # test.set_evaluating(train.get_state()) \
    #     .svc[('fea', 'target'), 'svm_evaluate_predict'](name='svm_classifier') \
    #     .with_metrics(['accuracy', 'recall']) \
    #     .evaluate['target', 'svm_evaluate_predict']('svm') \
    #     .report()

    def test_run(self):
        # pylint: disable=unnecessary-lambda
        x = []
        dc = reactive.range(2).stream().runas_op(func=lambda a: x.append(a))
        self.assertEqual(x, [])
        dc.run()
        self.assertEqual(x, [0, 1])


def load_tests(loader, tests, ignore):
    # pylint: disable=unused-argument
    tests.addTests(doctest.DocTestSuite(reactive.datacollection))
    tests.addTests(doctest.DocTestSuite(reactive.types.option))
    return tests


if __name__ == "__main__":
    unittest.main()
