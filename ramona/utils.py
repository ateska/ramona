import os, sys, re, signal, logging, itertools, glob, gzip
try:
	import resource
except ImportError:
	resource = None

###

L = logging.getLogger("utils")

###

def launch_server(server_only=True, programs=None, logfname=None):
	'''
This function launches Ramona server - in 'os.exec' manner which means that this function will not return
and instead of that, current process will be replaced by launched server. 

All file descriptors above 2 are closed.
	'''
	if server_only: assert (programs is None or len(programs) == 0)

	# Prepare environment variable RAMONA_CONFIG and RAMONA_CONFIG_FULL
	from .config import config_files, config_includes
	os.environ['RAMONA_CONFIG'] = os.pathsep.join(config_files)
	os.environ['RAMONA_CONFIG_WINC'] = os.pathsep.join(itertools.chain(config_files, config_includes))
	if logfname is not None: os.environ['RAMONA_LOGFILE'] = logfname

	# Prepare command line
	cmdline = ["-m", "ramona.server"]
	if server_only: cmdline.append('-S')
	elif programs is not None: cmdline.extend(programs)

	# Launch
	if sys.platform == 'win32':
		# Windows specific code, os.exec* process replacement is not possible, so we try to mimic that
		import subprocess
		ret = subprocess.call(get_python_exec(cmdline))
		sys.exit(ret)

	else:
		close_fds()
		pythonexec = get_python_exec()
		os.execl(pythonexec, os.path.basename(pythonexec), *cmdline)

#

def launch_server_daemonized():
	"""
This function launches Ramona server as a UNIX daemon.
It detaches the process context from parent (caller) and session.
This functions does return, launch_server() function doesn't due to exec() function in it.
	"""
	from .config import config

	logfname = config.get('ramona:server','log')
	if logfname.find('<logdir>') == 0:
		lastfname = logfname[8:].strip().lstrip('/')
		if len(lastfname) == 0: lastfname = 'ramona.log'
		logfname = os.path.join(config.get('general','logdir'), lastfname)
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

	launch_server(logfname=logfname)

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


def get_signal_name(signum):
	sigdict = dict((num, name) for name, num in signal.__dict__.iteritems() if name.startswith('SIG') and not name.startswith('SIG_'))
	ret = sigdict.get(signum)
	if ret is None: ret = "SIG({})".format(str(signum))
	return ret

###

def close_fds():
	'''
	Close all open file descriptors above standard ones. 
	This prevents the child from keeping open any file descriptors inherited from the parent.

	This function is executed only if platform supports that - otherwise it does nothing.
	'''
	if resource is None: return
	
	maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
	if (maxfd == resource.RLIM_INFINITY):
		maxfd = 1024

	os.closerange(3, maxfd)

###

if os.name == 'posix':
	import fcntl

	def enable_nonblocking(fd):
		fl = fcntl.fcntl(fd, fcntl.F_GETFL)
		fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

	def disable_nonblocking(fd):
		fl = fcntl.fcntl(fd, fcntl.F_GETFL)
		fcntl.fcntl(fd, fcntl.F_SETFL, fl ^ os.O_NONBLOCK)

elif sys.platform == 'win32':

	def enable_nonblocking(fd):
		raise NotImplementedError("utils.enable_nonblocking() not implementerd on Windows")

	def disable_nonblocking(fd):
		raise NotImplementedError("utils.disable_nonblocking() not implementerd on Windows")

###

_varprog = re.compile(r'\$(\w+|\{[^}]*\})')

def expandvars(path, env):
	"""Expand shell variables of form $var and ${var}.  Unknown variables are left unchanged.
	This is actually borrowed from os.path.expandvars (posixpath variant).
	"""

	if '$' not in path: return path
	i = 0

	while True:
        	m = _varprog.search(path, i)
        	if not m: break
        	i, j = m.span(0)
        	name = m.group(1)
		if name.startswith('{') and name.endswith('}'): name = name[1:-1]
		name=name.upper() # Use upper-case form for environment variables (e.g. Windows ${comspec})
		if name in env:
			tail = path[j:]
			path = path[:i] + env[name]
			i = len(path)
			path += tail
		else:
			i = j

	return path

###

def get_python_exec(cmdline=None):
	"""
	Return path for Python executable - similar to sys.executable but also handles corner cases on Win32

	@param cmdline: Optional command line arguments that will be added to python executable, can be None, string or list
	"""

	if sys.executable.lower().endswith('pythonservice.exe'):
		pythonexec = os.path.join(sys.exec_prefix, 'python.exe')
	else:
		pythonexec = sys.executable

	if cmdline is None: return pythonexec
	elif isinstance(cmdline, basestring): return pythonexec + ' ' + cmdline
	else: return " ".join([pythonexec] + cmdline)

###

def compress_logfile(fname):
	with open(fname, 'rb') as f_in, gzip.open('{0}.gz'.format(fname), 'wb') as f_out:
		f_out.writelines(f_in)
	os.unlink(fname)

#

_rotlognamerg = re.compile('\.([0-9]+)(\.gz)?$')

def rotate_logfiles(app, logfilename, logbackups, logcompress):
	fnames = set()
	suffixes = dict()
	for fname in glob.iglob(logfilename+'.*'):
		if not os.path.isfile(fname): continue
		x = _rotlognamerg.search(fname)
		if x is None: continue
		idx = int(x.group(1))
		suffix = x.group(2)
		if suffix is not None: 
			suffixes[idx] = suffix
		fnames.add(idx)

	for k in sorted(fnames, reverse=True):
		suffix = suffixes.get(k, "")
		if (logbackups > 0) and (k >= logbackups):
			os.unlink("{0}.{1}{2}".format(logfilename, k, suffix))
			continue
		if ((k-1) not in fnames) and (k > 1): continue # Move only files where there is one 'bellow'
		os.rename("{0}.{1}{2}".format(logfilename, k, suffix), "{0}.{1}{2}".format(logfilename, k+1, suffix))
		if logcompress and suffix != ".gz" and k+1 >= 2:
		 	app.add_idlework(compress_logfile, "{0}.{1}".format(logfilename, k+1))

	os.rename("{0}".format(logfilename), "{0}.1".format(logfilename))
