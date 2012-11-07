import unittest
import logging
from . import config
from . import sendmail
from . import utils
###
'''
To launch unit test:
python -m unittest -v ramona.__utest__
'''
###

class TestConfig(unittest.TestCase):


	def test_get_numeric_loglevel(self):
		'''Translating log level to numbers'''
		lvl = config.get_numeric_loglevel('Debug')
		self.assertEqual(lvl, logging.DEBUG)

		lvl = config.get_numeric_loglevel('ERROR')
		self.assertEqual(lvl, logging.ERROR)

		self.assertRaises(ValueError, config.get_numeric_loglevel, '')

#

class TestSendMail(unittest.TestCase):

	def test_get_default_fromaddr(self):
		sendmail.send_mail.get_default_fromaddr()


	def test_sendmail_uri_01(self):
		u = sendmail.send_mail('smtp://mail.example.com')
		self.assertEqual(u.hostname, 'mail.example.com')
		self.assertEqual(u.port, 25)
		self.assertIsNone(u.username)
		self.assertIsNone(u.password)
		self.assertDictEqual(u.params, {})


	def test_sendmail_uri_02(self):
		self.assertRaises(RuntimeError, sendmail.send_mail, 'xsmtp://smtp.t-email.cz')


	def test_sendmail_uri_03(self):
		self.assertRaises(RuntimeError, sendmail.send_mail, 'xsmtp:///dd')


	def test_sendmail_uri_04(self):
		'''Simulating Google SMTP parametrization'''
		u = sendmail.send_mail('smtp://user:password@smtp.gmail.com:587/;tls=1')
		self.assertEqual(u.hostname, 'smtp.gmail.com')
		self.assertEqual(u.port, 587)
		self.assertEqual(u.username, 'user')
		self.assertEqual(u.password, 'password')
		self.assertDictEqual(u.params, {'tls':'1'})

#

class TestExpandVars(unittest.TestCase):

	def test_expandvars_01(self):
		env = {'FOO':'bar'}
		
		p = utils.expandvars('/testing/$FOO/there', env)
		self.assertEqual(p, '/testing/bar/there')

		p = utils.expandvars('$FOO/there', env)
		self.assertEqual(p, 'bar/there')

		p = utils.expandvars('/testing/$FOO', env)
		self.assertEqual(p, '/testing/bar')


	def test_expandvars_02(self):
		env = {'FOO':'bar'}
		
		p = utils.expandvars('$XXX/testing/$FOO/there', env)
		self.assertEqual(p, '$XXX/testing/bar/there')

		p = utils.expandvars('$FOO/there$XXX', env)
		self.assertEqual(p, 'bar/there$XXX')

		p = utils.expandvars('/testing/$XX$FOO', env)
		self.assertEqual(p, '/testing/$XXbar')


	def test_expandvars_02(self):
		env = {'FOO':'bar'}
		
		p = utils.expandvars('$XXX/testing/${FOO}/there', env)
		self.assertEqual(p, '$XXX/testing/bar/there')

		p = utils.expandvars('${FOO}/there$XXX', env)
		self.assertEqual(p, 'bar/there$XXX')

		p = utils.expandvars('/testing/$XX${FOO}', env)
		self.assertEqual(p, '/testing/$XXbar')
