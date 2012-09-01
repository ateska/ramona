import logging, time
from ..config import config
from .program import program
from .seqctrl import sequence_controller

###

L = logging.getLogger('proaster')

###

class program_roaster(object):

	def __init__(self):
		self.start_seq = None
		self.roaster = []
		for config_section in config.sections():
			if config_section.find('program:') != 0: continue
			sp = program(self.loop, config_section)
			self.roaster.append(sp)


	def start_program(self):
		# Start processes that are STOPPED
		#TODO: Switch to allow starting state.FATAL programs too

		assert self.start_seq is None #TODO: Better handling of this situation
		#TODO: Also handle conflict with stop_pad
		L.debug("Initializing start sequence")
		self.start_seq = sequence_controller()

		for p in self.roaster:
			if p.state not in (program.state_enum.STOPPED,): continue
			self.start_seq.add(p)		

		self.__start_pad_next()


	def __start_pad_next(self):
		pg = self.start_seq.next()
		if pg is None:
			self.start_seq = None
			L.debug("Starting sequence completed.")
		else:
			# Start all programs in the active set
			map(program.start, pg)


	def stop_program(self):
		# Stop processes that are RUNNING and STARTING
		for p in self.roaster:
			if p.state not in (program.state_enum.RUNNING, program.state_enum.STARTING): continue
			p.stop()


	def restart_program(self):
		#TODO: This ...
		pass


	def on_terminate_program(self, pid, status):
		for p in self.roaster:
			if pid != p.pid: continue
			return p.on_terminate(status)
		else:
			L.warning("Unknown program died (pid={0}, status={1})".format(pid, status))


	def on_tick(self):
		'''Periodic check of program states'''
		now = time.time()
		for p in self.roaster:
			p.on_tick(now)

		if self.start_seq is not None:
			r = self.start_seq.check(program.state_enum.STARTING, program.state_enum.RUNNING)
			if r is None:
				L.warning("Starting sequence aborted due to program error")
			elif r: self.__start_pad_next()

