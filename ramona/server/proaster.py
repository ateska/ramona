import logging, time
from ..config import config
from ..cnscom import svrcall_error, program_state_enum
from .program import program
from .seqctrl import sequence_controller

###

L = logging.getLogger('proaster')
Lmy = logging.getLogger('my')

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
			sp = program(self, config_section)
			self.roaster.append(sp)


	def get_program(self, ident):
		for p in self.roaster:
			if p.ident == ident: return p
		raise KeyError("Unknown program '{0}' requested".format(ident))


	def filter_roaster_iter(self, pfilter=None):
		if pfilter is None:
			for p in self.roaster: yield p
			return

		filter_set = frozenset(pfilter)
		roaster_dict = dict((p.ident, p) for p in self.roaster)

		# Pass only known program names
		not_found = filter_set.difference(roaster_dict)
		if len(not_found) > 0:
			for pn in not_found:
				Lmy.error('Unknown/invalid program name: {0}'.format(pn))

		for ident, p in roaster_dict.iteritems():
			if ident in filter_set: yield p


	def start_program(self, cnscon, pfilter=None, force=False):
		'''Start processes that are STOPPED and (forced) FATAL'''
		if self.start_seq is not None or self.stop_seq is not None or self.restart_seq is not None:
			raise svrcall_error("There is already start/stop sequence running - please wait and try again later.")

		l = self.filter_roaster_iter(pfilter)

		L.debug("Initializing start sequence")
		self.start_seq = sequence_controller(cnscon)

		# If 'force' is used, include as programs in FATAL state
		if force: states = (program_state_enum.STOPPED,program_state_enum.FATAL)
		else: states = (program_state_enum.STOPPED,)

		for p in l:
			if p.state in states:
				self.start_seq.add(p)		
			else:
				Lmy.warning("Program {0} is in {1} state - not starting.".format(p.ident, program_state_enum.labels.get(p.state,'<?>')))

		self.__startstop_pad_next(True)


	def stop_program(self, cnscon, pfilter=None, force=False, coredump=False):
		'''
		Stop processes that are RUNNING and STARTING
		@param force: If True then it interrupts any concurrently running start/stop sequence.
		'''
		if force:
			self.start_seq = None
			self.restart_seq = None
			self.stop_seq = None

		else:
			if self.start_seq is not None or self.stop_seq is not None or self.restart_seq is not None:
				raise svrcall_error("There is already start/stop sequence running - please wait and try again later.")

		l = self.filter_roaster_iter(pfilter)

		L.debug("Initializing stop sequence")
		self.stop_seq = sequence_controller(cnscon)

		for p in l:
			if p.state not in (program_state_enum.RUNNING, program_state_enum.STARTING): continue
			if coredump: p.charge_coredump()
			self.stop_seq.add(p)

		self.__startstop_pad_next(False)


	def restart_program(self, cnscon, pfilter=None, force=False):
		'''Restart processes that are RUNNING, STARTING, STOPPED and (forced) FATAL'''
		if self.start_seq is not None or self.stop_seq is not None or self.restart_seq is not None:
			raise svrcall_error("There is already start/stop sequence running - please wait and try again later.")

		L.debug("Initializing restart sequence")
		
		l = self.filter_roaster_iter(pfilter)

		self.stop_seq = sequence_controller() # Don't need to have cnscon connected with stop_seq (there is no return)
		self.restart_seq = sequence_controller(cnscon)

		# If 'force' is used, include as programs in FATAL state
		if force: start_states = (program_state_enum.STOPPED,program_state_enum.FATAL)
		else: start_states = (program_state_enum.STOPPED,)

		for p in l:
			if p.state in (program_state_enum.RUNNING, program_state_enum.STARTING):
				self.stop_seq.add(p)
				self.restart_seq.add(p)
			elif p.state in start_states:
				self.restart_seq.add(p)
			else:
				Lmy.warning("Program {0} is in {1} state - not restarting.".format(p.ident, program_state_enum.labels.get(p.state,'<?>')))

		self.__startstop_pad_next(False)



	def __startstop_pad_next(self, start=True):
		pg = self.start_seq.next() if start else self.stop_seq.next()
		if pg is None:
			if start:
				cnscon = self.start_seq.cnscon
				if cnscon is not None:
					self.start_seq.cnscon = None
					cnscon.send_return(True)
				self.start_seq = None
				L.debug("Start sequence completed.")
			else:
				cnscon = self.stop_seq.cnscon

				if self.restart_seq is None or self.termstatus is not None:
					if cnscon is not None:
						self.stop_seq.cnscon = None
						cnscon.send_return(True)
					L.debug("Stop sequence completed.")
					self.stop_seq = None
					return

				else:
					Lmy.info("Restart finished stop phase and entering start phase")
					L.debug("Restart sequence enters starting phase")
					self.stop_seq = None
					self.start_seq = self.restart_seq
					self.restart_seq = None
					self.__startstop_pad_next(True)
					return

		else:
			# Start/stop all programs in the active set
			map(program.start if start else program.stop, pg)


	def on_terminate_program(self, pid, status):
		for p in self.roaster:
			if pid != p.pid: continue
			return p.on_terminate(status)
		else:
			L.warning("Unknown program died (pid={0}, status={1})".format(pid, status))


	def on_tick(self, now):
		'''Periodic check of program states'''
		for p in self.roaster:
			p.on_tick(now)

		if self.start_seq is not None:
			r = self.start_seq.check(program_state_enum.STARTING, program_state_enum.RUNNING)
			if r is None:
				L.warning("Start sequence aborted due to program error")
				self.start_seq = None
				assert self.restart_seq is None
			elif r:
				self.__startstop_pad_next(True)

		if self.stop_seq is not None:
			r = self.stop_seq.check(program_state_enum.STOPPING, program_state_enum.STOPPED)
			if r is None:
				if self.restart_seq is None:
					L.warning("Stop sequence aborted due to program error")
					self.stop_seq = None
					assert self.start_seq is None
					assert self.restart_seq is None
				else:
					L.warning("Restart sequence aborted due to program error")
					self.restart_seq = None
					self.stop_seq = None
					assert self.start_seq is None

			elif r:
				self.__startstop_pad_next(False)
