
class sequence_controller(object):
	'''
Start/Stop program sequence controller.
It is implementation of "SELECT * FROM programs GROUP BY priority" with a little bit of logic on top of that
	'''

	def __init__(self, cnscon = None):
		'''
		@param cnscon: Eventual console connection.
		'''
		super(sequence_controller, self).__init__()
		self.sequence = {}
		self.active = None
		self.cnscon = cnscon


	def __del__(self):
		if self.cnscon is not None:
			self.cnscon.send_exception(RuntimeError('Start/stop sequence terminated prematurely'))
			self.cnscon = None


	def add(self, program):
		sq = self.sequence.get(program.priority)
		if sq is None:
			self.sequence[program.priority] = sq = list()

		sq.append(program)


	def next(self):
		assert self.active is None
		try:
			mink=min(self.sequence.iterkeys())
		except ValueError:
			# We are at the end of the launch sequence
			return None
		self.active = self.sequence.pop(mink)
		return self.active[:] # Return copy (it is safer)


	def check(self, src_state, trg_state):
		'''
		@param state: target state for active set
		@return: 
			True if active set is 'ready to advance' (all in given 'state') to next program set
			False if not
			None if active set launch failed (and launchpad sequence is wasted)
		'''
		if self.active is None: return True

		res = True
		for a in self.active:
			if a.state == src_state: res = False
			elif a.state == trg_state: pass
			else: return None

		if res:self.active = None
		return res
