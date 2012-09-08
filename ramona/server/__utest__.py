import unittest
from .seqctrl import sequence_controller
from ..cnscom import program_state_enum
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
		sc.add(self._dummy_program('a',1))
		sc.add(self._dummy_program('b',2))
		sc.add(self._dummy_program('c',1))
		sc.add(self._dummy_program('d',2))
		sc.add(self._dummy_program('e',1))
		sc.add(self._dummy_program('f',4))

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
		sc.add(self._dummy_program('a',1))
		sc.add(self._dummy_program('b',2))
		sc.add(self._dummy_program('c',1))

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

