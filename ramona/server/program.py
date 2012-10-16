import sys, os, time, logging, shlex, signal, subprocess, errno
import pyev
from ..config import config, get_boolean
from ..utils import parse_signals, close_fds, expandvars, enable_nonblocking, disable_nonblocking
from ..cnscom import program_state_enum, svrcall_error
from .logmed import log_mediator

#

try:
	import resource
except ImportError:
	resource = None

#

L = logging.getLogger("program")
Lmy = logging.getLogger("my") # Message yielding logger

#

class program(object):

	DEFAULTS = {
		'command': None,
		'directory': None,
		'umask': None,
		'starttimeout': 0.5,
		'stoptimeout': 3,
		'killby': 'TERM,TERM,TERM,QUIT,QUIT,INT,INT,KILL',
		'stdin': '<null>',
		'stdout': '<stderr>',
		'stderr': '<logdir>',
		'priority': 100,
		'disabled': False,
		'coredump': False,
		'autorestart': False,
		'processgroup': True,
		'logscan_stdout': '',
		'logscan_stderr': '',
	}

	def __init__(self, svrapp, config_section):
		_, self.ident = config_section.split(':', 2)
		self.state = program_state_enum.STOPPED
		self.subproc = None

		self.launch_cnt = 0
		self.autorestart_cnt = 0
		self.start_time = None
		self.stop_time = None
		self.exit_time = None
		self.exit_status = None
		self.coredump_enabled = None # If true, kill by SIGQUIT -> dump core

		self.watchers = [
			pyev.Io(0, 0, svrapp.loop, self.__read_stdfd, 0),
			pyev.Io(0, 0, svrapp.loop, self.__read_stdfd, 1),
		]

		# Build configuration
		self.config = self.DEFAULTS.copy()
		self.config.update(config.items(config_section))

		cmd = self.config.get('command')
		if cmd is None:
			L.error("Missing command option in {0} -> CFGERROR".format(config_section))
			self.state = program_state_enum.CFGERROR
			return

		if cmd == '<httpfend>':
			cmd = '{0} -u -m ramona.httpfend'.format(sys.executable)
		elif cmd[:1] == '<':
			L.error("Unknown command option '{1}' in {0} -> CFGERROR".format(config_section, cmd))
			self.state = program_state_enum.CFGERROR
			return

		self.cmdline = shlex.split(cmd)
		self.stopsignals = parse_signals(self.config['killby'])
		if len(self.stopsignals) == 0: self.stopsignals = [signal.SIGTERM]
		self.act_stopsignals = None

		if self.config['stdin'] != '<null>':
			L.error("Unknown stdin option '{0}' in {1} -> CFGERROR".format(self.config['stdin'], config_section))
			self.state = program_state_enum.CFGERROR
			return

		try:
			self.priority = int(self.config.get('priority'))
		except:
			L.error("Invalid priority option '{0}' in {1} -> CFGERROR".format(self.config['priority'], config_section))
			self.state = program_state_enum.CFGERROR
			return		
		
		try:
			dis = get_boolean(self.config.get('disabled'))
		except ValueError:
			L.error("Unknown 'disabled' option '{0}' in {1} -> CFGERROR".format(dis, config_section))
			self.state = program_state_enum.CFGERROR
			return
		if dis:
			self.state = program_state_enum.DISABLED

		self.ulimits = {}
		#TODO: Enable other ulimits..
		try:
			coredump = get_boolean(self.config.get('coredump',False))
		except ValueError:
			L.error("Unknown 'coredump' option '{0}' in {1} -> CFGERROR".format(self.config.get('coredump','?'), config_section))
			self.state = program_state_enum.CFGERROR
			return

		if coredump and resource is not None:
			self.ulimits[resource.RLIMIT_CORE] = (-1,-1)

		try:
			self.autorestart = get_boolean(self.config.get('autorestart',False))
		except ValueError:
			L.error("Unknown 'autorestart' option '{0}' in {1} -> CFGERROR".format(self.config.get('autorestart','?'), config_section))
			self.state = program_state_enum.CFGERROR
			return

		try:
			get_boolean(self.config.get('processgroup',True))
		except ValueError:
			L.error("Unknown 'processgroup' option '{0}' in {1} -> CFGERROR".format(self.config.get('processgroup','?'), config_section))
			self.state = program_state_enum.CFGERROR
			return

		umask = self.config.get('umask')
		if umask is not None:
			try:
				umask = int(umask, 8)
			except:
				L.error("Invalid umask option ({1}) in {0} -> CFGERROR".format(config_section, umask))
				self.state = program_state_enum.CFGERROR
				return
			self.config['umask'] = umask


		# Prepare log files
		stdout_cnf = self.config['stdout']
		stderr_cnf = self.config['stderr']

		if (stdout_cnf == '<stderr>') and (stderr_cnf == '<stdout>'):
			L.error("Invalid stdout and stderr combination in {0} -> CFGERROR".format(config_section))
			self.state = program_state_enum.CFGERROR
			return			

		# Stdout settings
		if stdout_cnf == '<logdir>':
			if stderr_cnf  in ('<stderr>','<null>') :
				fname = os.path.join(config.get('general','logdir'), self.ident + '.log')
			else:
				fname = os.path.join(config.get('general','logdir'), self.ident + '-out.log')
			self.log_out = log_mediator(self.ident, 'stdout', fname)
		elif stdout_cnf == '<stderr>':
			pass
		elif stdout_cnf == '<null>':
			self.log_out = log_mediator(self.ident, 'stdout', None)
		elif stdout_cnf[:1] == '<':
			L.error("Unknown stdout option in {0} -> CFGERROR".format(config_section))
			self.state = program_state_enum.CFGERROR
			return			
		else:
			self.log_out = log_mediator(self.ident, 'stdout', stdout_cnf)

		# Stderr settings
		if stderr_cnf == '<logdir>':
			if stdout_cnf in ('<stderr>','<null>') :
				fname = os.path.join(config.get('general','logdir'), self.ident + '.log')
			else:
				fname = os.path.join(config.get('general','logdir'), self.ident + '-err.log')
			self.log_err = log_mediator(self.ident, 'stderr', fname)
		elif stderr_cnf == '<stdout>':
			self.log_err = self.log_out
		elif stderr_cnf == '<null>':
			self.log_err = log_mediator(self.ident, 'stderr', None)
		elif stderr_cnf[:1] == '<':
			L.error("Unknown stderr option in {0} -> CFGERROR".format(config_section))
			self.state = program_state_enum.CFGERROR
			return
		else:
			self.log_err = log_mediator(self.ident, 'stderr', stderr_cnf)

		if stdout_cnf == '<stderr>':
			self.log_out = self.log_err


		# Log scans
		for stream, logmed in [('stdout', self.log_out),('stderr', self.log_err)]:
			for logscanseg in self.config.get('logscan_{0}'.format(stream)).split(','):
				logscanseg = logscanseg.strip()
				if logscanseg == '': continue

				try:
					pattern, target = logscanseg.split('>',1)
				except ValueError:
					L.error("Unknown 'logscan_{2}' option '{0}' in {1} -> CFGERROR".format(logscanseg, config_section, stream))
					self.state = program_state_enum.CFGERROR
					return

				if target not in ('now','daily') and not target.startswith('mailto:'):
					L.error("Unknown 'logscan_{2}' option '{0}' in {1} -> CFGERROR".format(target, config_section, stream))
					self.state = program_state_enum.CFGERROR
					return

				logmed.add_scanner(pattern, target)


		# Environment variables
		self.env = os.environ.copy()
		if config.has_section('env'):
			for name, value in config.items('env'):
				if value != '':
					self.env[name] = value
				else:
					self.env.pop(name, 0)
		self.env['RAMONA_SECTION'] = config_section


	def __repr__(self):
		return "<{0} {1} state={2} pid={3}>".format(self.__class__.__name__, self.ident, program_state_enum.labels[self.state],self.subproc.pid if self.subproc is not None else '?')


	def start(self, reset_autorestart_cnt=True):
		'''Transition to state STARTING'''
		assert self.subproc is None
		assert self.state in (program_state_enum.STOPPED, program_state_enum.FATAL)

		L.debug("{0} -> STARTING".format(self))

		# Prepare working directory
		directory = self.config.get('directory')
		if directory is not None:
			directory = expandvars(directory, self.env)

		# Launch subprocess
		try:
			self.subproc = subprocess.Popen(
				[expandvars(arg, self.env) for arg in self.cmdline],
				stdin=None,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE,
				preexec_fn=self.__preexec_fn,
				close_fds=True,
				shell=False, #TOOD: This can/should be configurable in [program:x] section
				cwd=directory,
				env=self.env
			)
		except Exception, e:
			self.state = program_state_enum.FATAL
			Lmy.error("{0} failed to start (now in FATAL state): {1}".format(self.ident, e))
			L.error("{0} failed to start: {1} -> FATAL".format(self, e))
			return

		enable_nonblocking(self.subproc.stdout)
		self.watchers[0].set(self.subproc.stdout, pyev.EV_READ)
		self.watchers[0].start()

		enable_nonblocking(self.subproc.stderr)
		self.watchers[1].set(self.subproc.stderr, pyev.EV_READ)
		self.watchers[1].start()

		self.log_out.open()
		self.log_err.open()
		self.log_err.write("\n-=[ STARTING by Ramona on {0} ]=-\n".format(time.strftime("%Y-%m-%d %H:%M:%S")))
		self.state = program_state_enum.STARTING
		self.start_time = time.time()
		self.stop_time = None
		self.exit_time = None
		self.exit_status = None
		self.coredump_enabled = None
		self.launch_cnt += 1
		if reset_autorestart_cnt: self.autorestart_cnt = 0


	def __preexec_fn(self):
		# Launch in dedicated process group (optionally)
		if get_boolean(self.config.get('processgroup',True)):
			os.setsid()

		# Set umask
		umask = self.config.get('umask')
		if umask is not None:
			try:
				os.umask(umask)
			except Exception, e:
				os.write(2, "FATAL: Set umask {0} failed: {1}\n".format(umask, e))
				raise


		# Set ulimits
		if resource is not None:
			for k,v in self.ulimits.iteritems():
				try:
					resource.setrlimit(k,v)
				except Exception, e:
					os.write(2, "WARNING: Setting ulimit '{1}' failed: {0}\n".format(e, k))


	def stop(self):
		'''Transition to state STOPPING'''
		if self.state == program_state_enum.FATAL: return # This can happen and it is probably OK

		assert self.subproc is not None
		assert self.state in (program_state_enum.RUNNING, program_state_enum.STARTING)

		L.debug("{0} -> STOPPING".format(self))
		self.act_stopsignals = self.stopsignals[:]
		signal = self.get_next_stopsignal()
		try:
			if get_boolean(self.config.get('processgroup',True)):
				os.kill(-self.subproc.pid, signal) # Killing whole process group
			else:
				os.kill(self.subproc.pid, signal)
		except:
			pass
		self.state = program_state_enum.STOPPING
		self.stop_time = time.time()


	def on_terminate(self, status):
		self.exit_time = time.time()
		self.exit_status = status

		# Close process stdout and stderr pipes (including vacuum of actual content)
		self.watchers[0].stop()
		self.watchers[0].set(0, 0)
		disable_nonblocking(self.subproc.stdout)
		while True:
			signal.setitimer(signal.ITIMER_REAL, 0.5) # Set timeout for following operation
			try:
				data = os.read(self.subproc.stdout.fileno(), 4096)
			except OSError, e:
				if e.errno == errno.EINTR:
					L.warning("We have stall recovery situation on stdout socket of {0}".format(self))
					# This stall situation can happen when program shares stdout with its child
					# e.g. command=bash -c "echo ahoj1; tail -f /dev/null"
					break
				raise
			if len(data) == 0: break
			self.log_out.write(data)

		self.watchers[1].stop()
		self.watchers[1].set(0, 0)
		disable_nonblocking(self.subproc.stderr)
		while True:
			signal.setitimer(signal.ITIMER_REAL, 0.2) # Set timeout for following operation
			try:
				data = os.read(self.subproc.stderr.fileno(), 4096)
			except OSError, e:
				if e.errno == errno.EINTR:
					L.warning("We have stall recovery situation on stderr socket of {0}".format(self))
					# See comment above
					break
				raise
			if len(data) == 0: break
			self.log_err.write(data)

		# Explicitly destroy subprocess object
		self.subproc = None

		# Close log files
		self.log_err.write("\n-=[ EXITED on {0} with status {1} ]=-\n".format(time.strftime("%Y-%m-%d %H:%M:%S"), status))
		self.log_out.close()
		self.log_err.close()

		# Handle state change properly
		if self.state == program_state_enum.STARTING:
			Lmy.error("{0} exited too quickly (now in FATAL state)".format(self.ident))
			L.error("{0} exited too quickly -> FATAL".format(self))
			self.state = program_state_enum.FATAL

		elif self.state == program_state_enum.STOPPING:
			Lmy.info("{0} is now STOPPED".format(self.ident))
			L.debug("{0} -> STOPPED".format(self))
			self.state = program_state_enum.STOPPED

		else:
			if self.autorestart:
				Lmy.error("{0} exited unexpectedly and going to be restarted".format(self.ident))
				L.error("{0} exited unexpectedly -> FATAL -> autorestart".format(self))
				self.state = program_state_enum.FATAL
				self.autorestart_cnt += 1
				self.start(reset_autorestart_cnt=False)
			else:
				Lmy.error("{0} exited unexpectedly (now in FATAL state)".format(self.ident))
				L.error("{0} exited unexpectedly -> FATAL".format(self))
				self.state = program_state_enum.FATAL


	def on_tick(self, now):
		# Switch starting programs into running state
		if self.state == program_state_enum.STARTING:
			if now - self.start_time >= self.config['starttimeout']:
				Lmy.info("{0} is now RUNNING".format(self.ident))
				L.debug("{0} -> RUNNING".format(self))
				self.state = program_state_enum.RUNNING

		elif self.state == program_state_enum.STOPPING:
			if now - self.stop_time >= self.config['stoptimeout']:
				L.warning("{0} is still terminating - sending another signal".format(self))
				signal = self.get_next_stopsignal()
				try:
					if get_boolean(self.config.get('processgroup',True)):
						os.kill(-self.subproc.pid, signal) # Killing whole process group
					else:
						os.kill(self.subproc.pid, signal)
				except:
					pass


	def get_next_stopsignal(self):
		if self.coredump_enabled:
			self.coredump_enabled = None
			L.debug("Core dump enabled for {0} - using SIGQUIT".format(self))
			return signal.SIGQUIT
		if len(self.act_stopsignals) == 0: return signal.SIGKILL
		return self.act_stopsignals.pop(0)


	def __read_stdfd(self, watcher, revents):
		while 1:
			try:
				data = os.read(watcher.fd, 4096)
			except OSError, e:
				if e.errno == errno.EAGAIN: return # No more data to read (would block)
				raise

			if len(data) == 0: # File descriptor is closed
				watcher.stop()
				return 
			
			if watcher.data == 0: self.log_out.write(data)
			elif watcher.data == 1: self.log_err.write(data)


	def tail(self, cnscon, stream, lines=80, tailf=False):
		if self.state == program_state_enum.CFGERROR:
			raise svrcall_error("Program {0} is not correctly configured".format(self.ident))
		if stream == 'stdout':
			return self.log_out.tail(cnscon, lines, tailf)
		elif stream == 'stderr':
			return self.log_err.tail(cnscon, lines, tailf)
		else:
			raise ValueError("Unknown stream '{0}'".format(stream))


	def tailf_stop(self, cnscon, stream):
		if stream == 'stdout':
			return self.log_out.tailf_stop(cnscon)
		elif stream == 'stderr':
			return self.log_err.tailf_stop(cnscon)
		else:
			raise ValueError("Unknown stream '{0}'".format(stream))


	def charge_coredump(self):
		if resource is None:
			L.warning("This platform doesn't support core dumps.")
			return

		l = self.ulimits.get(resource.RLIMIT_CORE, (0,0))
		if l == (0,0):
			Lmy.warning("Program {0} is not configured to dump code".format(self.ident))
			return
		self.coredump_enabled = True
