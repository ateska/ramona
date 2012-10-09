import unittest
import logging
from . import config
from . import sendmail
###
'''
To launch unit test:
python -m unittest -v ramona.__utest__
'''
###

class TestConfig(unittest.TestCase):


	def test_get_numeric_loglevel(self):
		lvl = config.get_numeric_loglevel('Debug')
		self.assertEqual(lvl, logging.DEBUG)

		lvl = config.get_numeric_loglevel('ERROR')
		self.assertEqual(lvl, logging.ERROR)

		self.assertRaises(ValueError, config.get_numeric_loglevel, '')


	def test_get_default_fromaddr(self):
		sendmail.get_default_fromaddr()
