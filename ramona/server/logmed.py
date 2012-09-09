import collections

###

class logmediator(object):
	'''
	This object serves as mediator between program and its log files.

	It provides following functionality:
		- log rotation (TODO)
		- tail buffer (TODO)
		- seek for patterns in log stream and eventually trigger error mail
	'''

	maxtailbuflen = 64*1024 # 64Kb is max len. of tail buffer

	def __init__(self, fname):
		'''
		@param fname: name of connected log file, can be None if no log is connected
		'''
		self.fname = fname
		if self.fname is not None:
			self.outf = open(self.fname,'a')
		else:
			self.outf = None

		self.tailbuf = collections.deque()
		self.tailbuflen = 0


	def close(self):
		if self.outf is not None:
			self.outf.close()
			self.outf = None


	def write(self, data):
		if self.outf is not None:
			self.outf.write(data)
			self.outf.flush() #TODO: Maybe something more clever here can be better (check logging.StreamHandler)

		# Add data to tail buffer
		datalen = len(data)
		self.tailbuf.append((data, datalen))
		self.tailbuflen += datalen

		# Clean tail buffer - data that exceeds max. length
		while self.tailbuflen > self.maxtailbuflen:
			try:
				_, odatalen = self.tailbuf.popleft()
			except IndexError:
				self.tailbuflen = 0
				break

			self.tailbuflen -= odatalen


	def tail(self):
		ret = "".join(d for d,_ in self.tailbuf)
		return ret

# # Following code is just example
#
# Init:
# Log searching (just example)
#self.kmp = kmp_search('error')
#
# Use:
# if sourceid == 1:
# 	i = self.kmp.search(data)
# 	if i >= 0:
# 		# Pattern detected in the data
# 		pass
