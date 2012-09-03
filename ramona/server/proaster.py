import logging, time
from ..config import config
from ..cnscom import svrcall_error
from .program import program
from .seqctrl import sequence_controller

###

L = logging.getLogger('proaster')

###

class program_roaster(object):
	'''
Program roaster is object that control all configured programs, their start/stop operations etc.
	'''

	def __init__(self):
		self.start_seq = None
		self.stop_seq = None
		self.restart_seq = None

		self.roaster = []
		for config_section in config.sections():
			if config_section.find('program:') != 0: continue
			sp = program(self.loop, config_section)
			self.roaster.append(sp)


	def filter_roaster_iter(self, filter_list = None):
		if filter_list is None:
			for p in self.roaster: yield p
			return

		filter_set = frozenset(filter_list)
		roaster_dict = dict((p.ident, p) for p in self.roaster)

		# Pass only known program names
		not_found = filter_set.difference(roaster_dict)
		if len(not_found) > 0: raise svrcall_error("Unknown/invalid program names: {0}".format(', '.join(not_found)))

		for ident, p in roaster_dict.iteritems():
			if ident in filter_set: yield p


	def start_program(self, filter_list=None):
		'''Start processes that are STOPPED'''
		#TODO: Switch to allow starting state.FATAL programs too

		assert self.start_seq is None #TODO: Better handling of this situation
		assert self.stop_seq is None #TODO: Better handling of this situation
		assert self.restart_seq is None #TODO: Better handling of this situation

		l = self.filter_roaster_iter(filter_list)

		L.debug("Initializing start sequence")
		self.start_seq = sequence_controller()

		for p in l:
			if p.state not in (program.state_enum.STOPPED,): continue
			self.start_seq.add(p)		

		self.__startstop_pad_next(True)


	def stop_program(self, filter_list=None):
		'''Stop processes that are RUNNING and STARTING'''
		assert self.start_seq is None #TODO: Better handling of this situation
		assert self.stop_seq is None #TODO: Better handling of this situation
		assert self.restart_seq is None #TODO: Better handling of this situation

		l = self.filter_roaster_iter(filter_list)

		L.debug("Initializing stop sequence")
		self.stop_seq = sequence_controller()

		for p in l:
			if p.state not in (program.state_enum.RUNNING, program.state_enum.STARTING): continue
			self.stop_seq.add(p)		

		self.__startstop_pad_next(False)


	def restart_program(self, filter_list=None):
		'''Restart processes that are RUNNING, STARTING and STOPPED'''
		assert self.start_seq is None #TODO: Better handling of this situation
		assert self.stop_seq is None #TODO: Better handling of this situation
		assert self.restart_seq is None #TODO: Better handling of this situation
		L.debug("Initializing restart sequence")
		
		l = self.filter_roaster_iter(filter_list)

		self.stop_seq = sequence_controller()
		self.restart_seq = sequence_controller()

		for p in l:
			if p.state in (program.state_enum.RUNNING, program.state_enum.STARTING):
				self.stop_seq.add(p)
				self.restart_seq.add(p)
			elif p.state in (program.state_enum.STOPPED,):
				self.restart_seq.add(p)

		self.__startstop_pad_next(False)



	def __startstop_pad_next(self, start=True):
		pg = self.start_seq.next() if start else self.stop_seq.next()
		if pg is None:
			if start:
				self.start_seq = None
				L.debug("Start sequence completed.")
			else:
				self.stop_seq = None
				if self.restart_seq is None:
					L.debug("Stop sequence completed.")
				else:
					L.debug("Restart sequence enters starting phase")
					self.start_seq = self.restart_seq
					self.restart_seq = None
					self.__startstop_pad_next(True)
		else:
			# Start/stop all programs in the active set
			map(program.start if start else program.stop, pg)


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
				L.warning("Start sequence aborted due to program error")
				self.start_seq = None
				assert self.restart_seq is None
				return	

			elif r:
				self.__startstop_pad_next(True)

		if self.stop_seq is not None:
			r = self.stop_seq.check(program.state_enum.STOPPING, program.state_enum.STOPPED)
			if r is None:
				if self.restart_seq is None:
					L.warning("Stop sequence aborted due to program error")
					self.stop_seq = None
					assert self.start_seq is None
					assert self.restart_seq is None
					return
				else:
					L.warning("Restart sequence aborted due to program error")
					self.restart_seq = None
					self.stop_seq = None
					assert self.start_seq is None
					return

			elif r:
				self.__startstop_pad_next(False)
