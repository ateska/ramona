import os, sys, urlparse, socket, signal, resource, logging
###

L = logging.getLogger("utils")

###



def launch_server():
	'''
This function launches Ramona server - in 'os.exec' manner which means that this function will not return
and instead of that, current process will be replaced by launched server. 

All file descriptors above 2 are closed.
	'''
	from .config import config, config_files
	
	args = []
	for cfile in config_files:
		args.append('-c')
		args.append(cfile)
	
	# Close all open file descriptors above standard ones.  This prevents the child from keeping
	# open any file descriptors inherited from the parent.
	os.closerange(3, MAXFD)

	#TODO: Rewise following line - maybe config.get('server', 'svrname') is not viable concept
	#os.execl(sys.executable, config.get('server', 'svrname'), "-m", "ramona.server", *args)
	os.execl(sys.executable, sys.executable, "-m", "ramona.server", *args)

#

def launch_server_daemonized():
	"""
This function launches Ramona server as a UNIX daemon.
It detaches the process context from parent (caller) and session.
In comparison to launch_server() it returns.
	"""
	from .config import config

	logfname = config.get('server','log')
	if logfname == '<logdir>':
		logfname = os.path.join(config.get('general','logdir'), 'ramona.log')
	elif logfname[:1] == '<':
		L.error("Unknown log option in [server] section - server not started")
		return

	try:
		logf = open(logfname, 'a')
	except IOError, e:
		L.fatal("Cannot open logfile {0} for writing: {1}. Check the configuration in [server] section. Exiting.".format(logfname, e))
		return

	with logf:
		pid = os.fork()
		if pid > 0:
			return pid

		os.setsid()

		pid = os.fork()
		if pid > 0:
			os._exit(0)

		stdin = os.open(os.devnull, os.O_RDONLY)
		os.dup2(stdin, 0)

		os.dup2(logf.fileno(), 1) # Prepare stdout
		os.dup2(logf.fileno(), 2) # Prepare stderr
	launch_server()
	
		

###

class deleteing_unix_socket(socket.socket):
	'''
This class is used as wrapper to socket object that represent listening UNIX socket.
It added ability to delete socket file when destroyed.
	'''

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

###

def parse_signals(signals):
	ret = []
	signame2signum = dict((name, num) for name, num in signal.__dict__.iteritems() if name.startswith('SIG') and not name.startswith('SIG_'))
	for signame in signals.split(','):
		signame = signame.strip().upper()
		if not signame.startswith('SIG'): signame = 'SIG'+signame
		signum = signame2signum.get(signame)
		if signum is None: raise RuntimeError("Unknown signal '{0}'".format(signame))
		ret.append(signum)
	return ret

###

MAXFD = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
if (MAXFD == resource.RLIM_INFINITY): MAXFD = 1024
