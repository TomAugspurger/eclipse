import unittest

import stactools.eclipse


class TestModule(unittest.TestCase):

    def test_version(self):
        self.assertIsNotNone(stactools.eclipse.__version__)
