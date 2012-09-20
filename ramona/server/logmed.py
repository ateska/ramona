import re, collections, io, os, glob, logging
from ..config import config
from ..kmpsearch import kmp_search
from .svrappsingl import get_svrapp

###

L = logging.getLogger('logmed')

###


class log_mediator(object):
	'''
	This object serves as mediator between program and its log files.

	It provides following functionality:
		- log rotation
		- tail buffer (TODO)
		- seek for patterns in log stream and eventually trigger error mail
	'''

	maxtailbuflen = 64*1024 # 64Kb is max len. of tail buffer
	rotlognamerg = re.compile('\.([0-9]+)$')

	def __init__(self, prog_ident, stream_name, fname):
		'''
		@param prog_ident: identification of the program (x from [program:x])
		@param stream_name: stdout or stderr
		@param fname: name of connected log file, can be None if no log is connected
		'''
		self.prog_ident = prog_ident
		self.stream_name = stream_name
		self.fname = fname
		self.outf = None
		self.scanners = []

		self.tailbuf = collections.deque()
		self.tailbuflen = 0

		# Read last content of the file into tail buffer
		if self.fname is not None and os.path.isfile(self.fname):
			with io.open(self.fname, 'r') as logf:
				if logf.seekable(): 
					logf.seek(0, io.SEEK_END)
					d = max(logf.tell() - self.maxtailbuflen, 0)
					logf.seek(d, io.SEEK_SET) # Seek to tail start position (end of file - maxtailbuflen)
					while True: # Read line by line into tail buffer
						data = logf.readline(4096)
						datalen = len(data)
						if datalen == 0: break
						self.__add_to_tailbuf(data)

		# Configure log rotation
		try:
			self.logmaxsize = config.getint('general','logmaxsize')
			self.logbackups = config.getint('general','logbackups')
		except Exception, e:
			self.logbackups = self.logmaxsize = 0
			L.warning("Invalid configuration of log rotation: {0} - log rotation disabled".format(e))


	def open(self):
		if self.outf is None and self.fname is not None:
			self.outf = open(self.fname,'a')
			

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
		if len(self.scanners) > 0:
			stext = data.lower()
			for s in self.scanners:
				r = s.search(stext)
				if r < 0: continue

				# Take last three tail entries (very likely lines)
				tail = ""
				for i in range(-3,0):
					try:
						tail += self.tailbuf[i][0]
					except IndexError:
						pass
				tail = tail[-2048:] # Limit result to 2kb of text

				svrapp = get_svrapp()
				if svrapp is not None:
					svrapp.notificator.publish(
						s.target,
						s.prog_ident,
						s.stream_name,
						''.join(s.pattern),
						tail
					)



	def rotate(self):
		'Perform rotation of connected file - if any'
		if self.fname is None: return
		if self.outf is None: return
		L.debug("Rotating '{0}' file".format(self.fname))

		self.outf.close()
		try:

			fnames = set()
			for fname in glob.iglob(self.fname+'.*'):
				if not os.path.isfile(fname): continue
				x = self.rotlognamerg.search(fname)
				if x is None: continue
				fnames.add(int(x.group(1)))

			for k in sorted(fnames, reverse=True):
				if (self.logbackups > 0) and (k >= self.logbackups):
					os.unlink("{0}.{1}".format(self.fname, k))
					continue
				if ((k-1) not in fnames) and (k > 1): continue # Move only files where there is one 'bellow'
				os.rename("{0}.{1}".format(self.fname, k), "{0}.{1}".format(self.fname, k+1))

			os.rename("{0}".format(self.fname), "{0}.1".format(self.fname))

		finally:
			self.outf = open(self.fname,'a')		


	def __add_to_tailbuf(self, data):
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
		d = collections.deque()
		dlen = 0
		for data, datalen in reversed(self.tailbuf):
			dlen += datalen
			if dlen >= 0x7fff: break #Protect maximum IPC data len
			d.appendleft(data)

		return "".join(d)


	def add_scanner(self, pattern, target):
		self.scanners.append(
			_log_scanner(self.prog_ident, self.stream_name, pattern, target)
		)


class _log_scanner(kmp_search):

	def __init__(self, prog_ident, stream_name, pattern, target):
		kmp_search.__init__(self, pattern)
		assert target in ('now','daily') or target.startswith('mailto:')
		self.target = target
		self.prog_ident = prog_ident
		self.stream_name = stream_name

