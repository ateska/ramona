import unittest
from .seqctrl import sequence_controller
from ..cnscom import program_state_enum
from .logmed import log_mediator
###
'''
To launch unit test:
python -m unittest -v ramona.server.__utest__
'''
###

class TestSequenceController(unittest.TestCase):


	class _dummy_program(object):

		def __init__(self, ident, prio):
			self.ident = ident
			self.priority = prio
			self.state = program_state_enum.STOPPED


	def test_HappyFlow(self):
		sc = sequence_controller()

		# Build launchpad sequence
		sc.add(self._dummy_program('a',9))
		sc.add(self._dummy_program('b',8))
		sc.add(self._dummy_program('c',9))
		sc.add(self._dummy_program('d',8))
		sc.add(self._dummy_program('e',9))
		sc.add(self._dummy_program('f',6))

		# Get first set
		actps = sc.next()
		pset = set(p.ident for p in actps)
		self.assertSetEqual(pset,{'a','c','e'})

		# Cannot continue to next one till got response
		self.assertRaises(AssertionError, sc.next)

		# Simulate start of active set and check that
		for p in actps: p.state = program_state_enum.STARTING
		r = sc.check(program_state_enum.STARTING, program_state_enum.RUNNING)
		self.assertFalse(r)
		self.assertRaises(AssertionError, sc.next)

		# Simulate sequential start of programs
		actps[0].state = program_state_enum.RUNNING
		r = sc.check(program_state_enum.STARTING, program_state_enum.RUNNING)
		self.assertFalse(r)
		self.assertRaises(AssertionError, sc.next)

		actps[1].state = program_state_enum.RUNNING
		r = sc.check(program_state_enum.STARTING, program_state_enum.RUNNING)
		self.assertFalse(r)
		self.assertRaises(AssertionError, sc.next)

		actps[2].state = program_state_enum.RUNNING
		r = sc.check(program_state_enum.STARTING, program_state_enum.RUNNING)
		self.assertTrue(r)

		# Now advancing to the next set
		actps = sc.next()
		pset = set(p.ident for p in actps)
		self.assertSetEqual(pset,{'b','d'})

		# Simulate sequential start of programs
		actps[0].state = program_state_enum.RUNNING
		r = sc.check(program_state_enum.STARTING, program_state_enum.RUNNING)
		self.assertFalse(r)
		self.assertRaises(AssertionError, sc.next)

		actps[1].state = program_state_enum.RUNNING
		r = sc.check(program_state_enum.STARTING, program_state_enum.RUNNING)
		self.assertTrue(r)

		# Third step
		actps = sc.next()
		pset = set(p.ident for p in actps)
		self.assertSetEqual(pset,{'f'})

		actps[0].state = program_state_enum.RUNNING
		r = sc.check(program_state_enum.STARTING, program_state_enum.RUNNING)
		self.assertTrue(r)

		actps = sc.next()
		self.assertIsNone(actps)


	def test_LaunchFailure(self):
		sc = sequence_controller()

		# Build launchpad sequence
		sc.add(self._dummy_program('a',9))
		sc.add(self._dummy_program('b',8))
		sc.add(self._dummy_program('c',9))

		# Get first set
		actps = sc.next()
		pset = set(p.ident for p in actps)
		self.assertSetEqual(pset,{'a','c'})

		# Simulate start of active set and check that
		for p in actps: p.state = program_state_enum.STARTING
		r = sc.check(program_state_enum.STARTING, program_state_enum.RUNNING)
		self.assertFalse(r)
		self.assertRaises(AssertionError, sc.next)

		# Simulate sequential start of programs
		actps[0].state = program_state_enum.FATAL
		r = sc.check(program_state_enum.STARTING, program_state_enum.RUNNING)

		self.assertIsNone(r)

#

class TestLogMediator(unittest.TestCase):


	def test_LogMediatorBasic(self):
		'Constructing log mediator'

		lm = log_mediator('foo_prog', 'stdout', None)
		lm.open()
		lm.write('Line1\n')
		lm.write('Line2\n')
		lm.write('Line3\n')
		lm.close()


	def test_LogMediatorLineTail(self):
		'Log mediator line separator'

		lm = log_mediator('foo_prog', 'stdout', None)
		lm.open()

		lm.write('Line')
		self.assertItemsEqual(lm.tailbuf, ['Line'])
		lm.write(' One')
		self.assertItemsEqual(lm.tailbuf, ['Line One'])
		lm.write('\n')
		self.assertItemsEqual(lm.tailbuf, ['Line One\n'])

		lm.write('Line 2\n')
		self.assertItemsEqual(lm.tailbuf, [
			'Line One\n',
			'Line 2\n',
		])

		lm.write('3Line')
		self.assertEqual(lm.tailbuf[-1], '3Line')
		lm.write(' 3')
		self.assertEqual(lm.tailbuf[-1], '3Line 3')
		lm.write('\n')
		self.assertItemsEqual(lm.tailbuf, [
			'Line One\n',
			'Line 2\n',
			'3Line 3\n',
		])

		lm.write('Line 4\nLine 5\nLine 6\n')
		self.assertItemsEqual(lm.tailbuf, [
			'Line One\n',
			'Line 2\n',
			'3Line 3\n',
			'Line 4\n',
			'Line 5\n',
			'Line 6\n',
		])

		lm.write('Line 7\nLine 8\nLine 9')

		self.assertItemsEqual(lm.tailbuf, [
			'Line One\n',
			'Line 2\n',
			'3Line 3\n',
			'Line 4\n',
			'Line 5\n',
			'Line 6\n',
			'Line 7\n',
			'Line 8\n',
			'Line 9',
		])

		lm.close()


	def test_LogMediatorLongLineTail(self):
		'Log mediator line separator (long lines)'

		lm = log_mediator('foo_prog', 'stdout', None)
		lm.open()

		lm.write('Line 1\n')
		self.assertItemsEqual(lm.tailbuf, ['Line 1\n'])

		lm.write('X'*60000)
		self.assertEqual(len(lm.tailbuf), 3)
		self.assertEqual(lm.tailbuf[1], 'X' * 32512)
		self.assertEqual(lm.tailbuf[2], 'X' * 27488)

		lm.write('X'*60000)
		self.assertEqual(len(lm.tailbuf), 5)
		self.assertEqual(lm.tailbuf[1], 'X' * 32512)
		self.assertEqual(lm.tailbuf[2], 'X' * 32512)
		self.assertEqual(lm.tailbuf[3], 'X' * 32512)
		self.assertEqual(lm.tailbuf[4], 'X' * 22464)

		lm.write('X\n')
		self.assertEqual(len(lm.tailbuf), 5)
		self.assertEqual(lm.tailbuf[4], 'X' * 22465 + '\n')

		lm.close()
