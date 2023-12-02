import unittest

import reactive as rv


class TestExceptionSafe(unittest.TestCase):
    """
    Unit test for exception safe.
    """

    def test_safe(self):
        retval = (
            rv.of["x"]([5, 3, 2, 1, 0])
            .safe()
            .runas_op["x", "x2"](lambda x: x - 1)
            .runas_op["x2", "y"](lambda x: 10 / x)
            .drop_empty()
            .runas_op(lambda x: x.y)
            .to_list()
        )
        self.assertListEqual(retval, [2.5, 5.0, 10.0, -10.0])


if __name__ == "__main__":
    unittest.main()
