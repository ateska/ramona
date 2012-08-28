import os, sys, urlparse, socket
###

def daemonize():
	""" Detach the process context from parent and session.

	Detach from the parent process and session group, allowing the
	parent to exit while this process continues running.

	Reference: "Advanced Programming in the Unix Environment",
	section 13.3, by W. Richard Stevens, published 1993 by
	Addison-Wesley.


	@return: pid ( > 0) - for 'parent' process and 0 for daemonized process
	"""

	pid = os.fork()
	if pid > 0:
		return pid

	os.setsid()

	pid = os.fork()
	if pid > 0:
		sys.exit(0)

	return 0

###

def launch_server():
	from .config import config, config_files
	
	args = []
	for cfile in config_files:
		args.append('-c')
		args.append(cfile)
	
	os.execl(sys.executable, config.get('server', 'svrname'), "-m", "ramona.server", *args)

###

class deleteing_unix_socket(socket.socket):


	def __init__(self):
		socket.socket.__init__(self, socket.AF_UNIX, socket.SOCK_STREAM)
		self.__sockfile = None


	def __del__(self):
		if self.__sockfile is not None:
			fname = self.__sockfile
			self.__sockfile = None
			os.unlink(fname)
			assert not os.path.isfile(fname)


	def bind(self, fname):
		socket.socket.bind(self, fname)
		self.__sockfile = fname

###

class socket_uri(object):
	'''
Socket factory that is configured using socket URI.
	'''

	# Configure urlparce
	if 'unix' not in urlparse.uses_params: urlparse.uses_params.append('unix')

	def __init__(self, uri):
		self.uri = urlparse.urlparse(uri)
		self.uriparams = dict(urlparse.parse_qsl(self.uri.params))

		self.protocol = self.uri.scheme.lower()
		if self.protocol == 'tcp':
			try:
				_port = self.uri.port
			except ValueError:
				raise RuntimeError("Invalid port number in socket URI {0}".format(uri))

			if self.uri.path != '': raise RuntimeError("Path has to be empty in socket URI {0}".format(uri))

		elif self.protocol == 'unix':
			pass

		else:
			raise RuntimeError("Unknown/unsuported protocol '{0}' in socket URI {1}".format(self.protocol, uri))


	def create_socket_listen(self):
		if self.protocol == 'tcp':
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			s.bind((self.uri.hostname, self.uri.port))

		elif self.protocol == 'unix':
			mode = self.uriparams.get('mode',None)
			if mode is None: mode = 0o600
			else: mode = int(mode,8)
			oldmask = os.umask(mode ^ 0o777)
			s = deleteing_unix_socket()
			s.bind(self.uri.path)
			os.umask(oldmask)

		else:
			raise RuntimeError("Unknown/unsuported protocol '{0}'".format(self.protocol))
		
		return s


	def create_socket_connect(self):
		if self.protocol == 'tcp':
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((self.uri.hostname, self.uri.port))

		elif self.protocol == 'unix':
			s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
			s.connect(self.uri.path)

		else:
			raise RuntimeError("Unknown/unsuported protocol '{0}'".format(self.protocol))
		
		return s
