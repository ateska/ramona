import os, sys, signal, resource, fcntl, logging
###

L = logging.getLogger("utils")

###

def launch_server():
	'''
This function launches Ramona server - in 'os.exec' manner which means that this function will not return
and instead of that, current process will be replaced by launched server. 

All file descriptors above 2 are closed.
	'''
	from .config import config_files

	env = os.environ.copy()
	env['RAMONA_CONFIG'] = ':'.join(config_files)
	
	# Close all open file descriptors above standard ones.  This prevents the child from keeping
	# open any file descriptors inherited from the parent.
	os.closerange(3, MAXFD)

	os.execle(sys.executable, sys.executable, "-m", "ramona.server", env)

#

def launch_server_daemonized():
	"""
This function launches Ramona server as a UNIX daemon.
It detaches the process context from parent (caller) and session.
In comparison to launch_server() it returns.
	"""
	from .config import config

	logfname = config.get('ramona:server','log')
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

###

def enable_nonblocking(fd):
	fl = fcntl.fcntl(fd, fcntl.F_GETFL)
	fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

def disable_nonblocking(fd):
	fl = fcntl.fcntl(fd, fcntl.F_GETFL)
	fcntl.fcntl(fd, fcntl.F_SETFL, fl ^ os.O_NONBLOCK)

