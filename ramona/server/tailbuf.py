
class tailbuf(object):

	def __init__(self, fname):
		'''
		@param fname: name of connected log file, can be None if no log is connected
		'''
		self.fname = fname
		if self.fname is not None:
			self.outf = open(self.fname,'a')
		else:
			self.outf = None


	def close(self):
		if self.outf is not None:
			self.outf.close()
			self.outf = None


	def write(self, data):
		if self.outf is not None:
			self.outf.write(data)
			self.outf.flush() #TODO: Maybe something more clever here can be better (check logging.StreamHandler)

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
