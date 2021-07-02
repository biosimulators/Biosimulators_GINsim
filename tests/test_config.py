from biosimulators_boolnet.config import Config
from unittest import mock
import os
import unittest


class ConfigTestCase(unittest.TestCase):
    def test_Config(self):
        with mock.patch.dict(os.environ, {'BOOLNET_VERSION': '2.1.5'}):
            self.assertEqual(Config().boolnet_version, '2.1.5')

        with mock.patch.dict(os.environ, {'BOOLNET_VERSION': ''}):
            self.assertEqual(Config().boolnet_version, None)
