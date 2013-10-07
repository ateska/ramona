import collections, os, weakref, logging
from ..config import get_logconfig
from ..kmpsearch import kmp_search
from ..utils import rotate_logfiles
from .singleton import get_svrapp

###

L = logging.getLogger('logmed')
Lmy = logging.getLogger("my") # Message yielding logger

###


class log_mediator(object):
	'''
	This object serves as mediator between program and its log files.

	It provides following functionality:
		- log rotation
		- tail buffer
		- seek for patterns in log stream and eventually trigger error mail
	'''

	maxlinelen = 0x7f00 # Connected to maximum IPC (console-server) data buffer
	linehistory = 100 # Number of tail history (in lines)

	def __init__(self, prog_ident, stream_name, fname):
		'''
		@param prog_ident: identification of the program (x from [program:x])
		@param stream_name: stdout or stderr
		@param fname: name of connected log file, can be None if no log is connected
		'''
		self.prog_ident = prog_ident
		self.stream_name = stream_name
		self.fname = os.path.normpath(fname) if fname is not None else None
		self.outf = None
		self.scanners = []

		self.tailbuf = collections.deque() # Lines
		self.tailbufnl = True
		self.tailfset = weakref.WeakSet()


		# Read last content of the file into tail buffer
		if self.fname is not None and os.path.isfile(self.fname):
			with open(self.fname, "r") as logf:
				logf.seek(0, os.SEEK_END)
				fsize = logf.tell()
				fsize -= self.linehistory * 512
				if fsize <0: fsize = 0
				logf.seek(fsize, os.SEEK_SET)
				
				for line in logf:
					self.__add_to_tailbuf(line)


		# Configure log rotation
		self.logbackups, self.logmaxsize, self.logcompress = get_logconfig()


	def open(self):
		if self.outf is None and self.fname is not None:
			try:
				self.outf = open(self.fname,'a')
			except Exception, e:
				L.warning("Cannot open log file '{0}' for {1}: {2}".format(self.fname, self.stream_name, e))
				Lmy.warning("Cannot open log file '{0}' for {1}: {2}".format(self.fname, self.stream_name, e))
				self.outf = None
				return False

		return True


	def close(self):
		if self.outf is not None:
			self.outf.close()
			self.outf = None


	def write(self, data):
		if self.outf is not None:
			self.outf.write(data)
			self.outf.flush() #TODO: Maybe something more clever here can be better (check logging.StreamHandler)
			if (self.logmaxsize > 0) and (self.outf.tell() >= self.logmaxsize):
				self.rotate()

		self.__add_to_tailbuf(data)

		# Search for patterns
		svrapp = get_svrapp()
		if len(self.scanners) > 0 and svrapp is not None:

			stext = data.lower()
			for s in self.scanners:

				startpos = s.startpos
				r = s.search(stext)
				if r < 0: continue

				# Calculate position in the stream
				startpos = r - startpos
				if startpos < 0: startpos = 0

				# Identify starting position 
				errstart = startpos
				for _ in range(3): # Number of lines before pattern hit
					errstart = stext.rfind('\n', 0, errstart)
					if errstart < 0:
						errstart = 0
						break

				# Identify end position 
				errend = startpos
				for _ in range(3):
					errend = stext.find('\n', errend+1)
					if errend < 0:
						errend = -1
						break
				
				pattern = ''.join(s.pattern)
				ntftext  = 'Program: {0}\n'.format(s.prog_ident)
				ntftext += 'Pattern: {0}\n'.format(pattern)
				ntftext += '\n'+'-'*50+'\n'
				ntftext += data[errstart:errend].strip('\n')
				ntftext += '\n'+'-'*50+'\n'

				svrapp.notificator.publish(s.target, ntftext, "{} / {}".format(s.prog_ident, pattern))


	def rotate(self):
		'Perform rotation of connected file - if any'
		if self.fname is None: return
		if self.outf is None: return

		L.debug("Rotating '{0}' file".format(self.fname))

		self.outf.close()
		try:
			rotate_logfiles(get_svrapp(), self.fname, self.logbackups, self.logcompress)
		finally:
			self.outf = open(self.fname,'a')		


	def __tailbuf_append(self, data, nlt):
		if self.tailbufnl:
			if len(data) <= self.maxlinelen:
				self.tailbuf.append(data)
			else:
				self.tailbuf.extend(_chunker(data, self.maxlinelen))

		else:
			data = self.tailbuf.pop() + data
			if len(data) <= self.maxlinelen:
				self.tailbuf.append(data)
			else:
				self.tailbuf.extend(_chunker(data, self.maxlinelen))

		self.tailbufnl = nlt

		# Remove old tail lines
		while len(self.tailbuf) > self.linehistory:
			self.tailbuf.popleft()


	def __add_to_tailbuf(self, data):
		# Add data to tail buffer
		lendata = len(data)
		if lendata == 0: return

		datapos = 0
		while datapos < lendata:
			seppos = data.find('\n', datapos)
			if seppos == -1:
				# Last chunk & no \n at the end
				if datapos == 0:
					self.__tailbuf_append(data, False)
				else:
					self.__tailbuf_append(data[datapos:], False)
				break
			elif seppos == lendata-1:
				# Last chunk terminated with \n
				if datapos == 0:
					self.__tailbuf_append(data, True)
				else:
					self.__tailbuf_append(data[datapos:], True)
				break
			else:
				self.__tailbuf_append(data[datapos:seppos+1], True)
				datapos = seppos + 1

		# Send tail to tailf clients
		for cnscon in self.tailfset:
			cnscon.send_tailf(data)


	def tail(self, cnscon, lines, tailf):
		d = collections.deque()
		dlen = 0
		for line in reversed(self.tailbuf):
			dlen += len(line)
			if dlen >= 0x7fff: break #Protect maximum IPC data len
			d.appendleft(line)
			lines -= 1
			if lines <=0: break

		if tailf:
			cnscon.tailf_enabled = True
			self.tailfset.add(cnscon)

		return "".join(d)


	def tailf_stop(self, cnscon):
		self.tailfset.remove(cnscon)
		cnscon.tailf_enabled = False


	def add_scanner(self, pattern, target):
		self.scanners.append(
			_log_scanner(self.prog_ident, self.stream_name, pattern, target)
		)

#

class _log_scanner(kmp_search):

	def __init__(self, prog_ident, stream_name, pattern, target):
		kmp_search.__init__(self, pattern)
		assert target.startswith(('now','daily'))
		self.target = target
		self.prog_ident = prog_ident
		self.stream_name = stream_name

#

def _chunker(data, maxsize):
	for i in xrange(0, len(data), maxsize):
		yield data[i:i+maxsize]

