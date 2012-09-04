import sys, os, time, logging, shlex, signal, resource, errno
import pyev
from ..config import config
from ..utils import parse_signals, MAXFD, enable_nonblocking, disable_nonblocking
from ..kmpsearch import kmp_search

#

L = logging.getLogger("subproc")

#

class program(object):

	DEFAULTS = {
		'command': None,
		'starttimeout': 0.5,
		'stoptimeout': 3,
		'stopsignal': 'INT,TERM,KILL',
		'stdin': '<null>',
		'stdout': '<stderr>',
		'stderr': '<logdir>',
		'priority': 100,
	}


	class state_enum:
		'''Enum'''
		STOPPED = 0
		STARTING = 10
		RUNNING = 20
		STOPPING = 30
		FATAL = 200
		CFGERROR=201

		labels = {
			STOPPED: 'STOPPED',
			STARTING: 'STARTING',
			RUNNING: 'RUNNING',
			STOPPING: 'STOPPING',
			FATAL: 'FATAL',
			CFGERROR: 'CFGERROR',
		}


	def __init__(self, loop, config_section):
		_, self.ident = config_section.split(':', 2)
		self.state = program.state_enum.STOPPED
		self.pid = None

		self.launch_cnt = 0
		self.start_time = None
		self.stop_time = None
		self.term_time = None

		self.stdout = None
		self.stderr = None
		self.watchers = [
			pyev.Io(0, 0, loop, self.__read_stdfd, 0),
			pyev.Io(0, 0, loop, self.__read_stdfd, 1),
		]

		# Build configuration
		self.config = self.DEFAULTS.copy()
		self.config.update(config.items(config_section))

		cmd = self.config.get('command')
		if cmd is None:
			L.fatal("Program {0} doesn't specify command - don't know how to launch it".format(self.ident))
			sys.exit(2)

		self.cmdline = shlex.split(cmd)
		self.stopsignals = parse_signals(self.config['stopsignal'])
		if len(self.stopsignals) == 0: self.stopsignals = [signal.SIGTERM]
		self.act_stopsignals = None

		if self.config['stdin'] != '<null>':
			L.error("Unknown stdin option '{0}' in {1} -> CFGERROR".format(self.config['stdin'], config_section))
			self.state = program.state_enum.CFGERROR
			return

		try:
			self.priority = int(self.config.get('priority'))
		except:
			L.error("Invalid priority option '{0}' in {1} -> CFGERROR".format(self.config['priority'], config_section))
			self.state = program.state_enum.CFGERROR
			return			

		# Prepare log files
		stdout_cnf = self.config['stdout']
		stderr_cnf = self.config['stderr']

		if (stdout_cnf == '<stderr>') and (stderr_cnf == '<stdout>'):
			L.error("Invalid stdout and stderr combination in {0} -> CFGERROR".format(config_section))
			self.state = program.state_enum.CFGERROR
			return			

		# Stdout settings
		self.log_out = None
		if stdout_cnf == '<logdir>':
			if stderr_cnf  in ('<stderr>','<null>') :
				self.log_out_fname = os.path.join(config.get('general','logdir'), self.ident + '.log')
			else:
				self.log_out_fname = os.path.join(config.get('general','logdir'), self.ident + '-out.log')
		elif stdout_cnf == '<stderr>':
			self.log_out_fname = None
		elif stdout_cnf == '<null>':
			self.log_out_fname = None
		elif stdout_cnf[:1] == '<':
			L.error("Unknown stdout option in {0} -> CFGERROR".format(config_section))
			self.state = program.state_enum.CFGERROR
			return			
		else:
			self.log_out_fname = stdout_cnf

		# Stderr settings
		self.log_err = None
		if stderr_cnf == '<logdir>':
			if stdout_cnf in ('<stderr>','<null>') :
				self.log_err_fname = os.path.join(config.get('general','logdir'), self.ident + '.log')
			else:
				self.log_err_fname = os.path.join(config.get('general','logdir'), self.ident + '-err.log')
		elif stderr_cnf == '<stdout>':
			self.log_err_fname = None
		elif stderr_cnf == '<null>':
			self.log_err_fname = None
		elif stderr_cnf[:1] == '<':
			L.error("Unknown stderr option in {0} -> CFGERROR".format(config_section))
			self.state = program.state_enum.CFGERROR
			return
		else:
			self.log_err_fname = stderr_cnf

		# Environment variables
		self.env = os.environ.copy()
		if config.has_section('env'):
			for name, value in config.items('env'):
				if value != '':
					self.env[name] = value
				else:
					self.env.pop(name, 0)
		self.env['RAMONA_SECTION'] = config_section

		# Log searching (just example)
		self.kmp = kmp_search('error')


	def __repr__(self):
		return "<{0} {1} state={2} pid={3}>".format(self.__class__.__name__, self.ident, program.state_enum.labels[self.state],self.pid if self.pid is not None else '?')


	def spawn(self, cmd, args):
		self.stdout, stdout = os.pipe()
		self.stderr, stderr = os.pipe()

		pid = os.fork()
		if pid !=0:
			os.close(stdout)
			os.close(stderr)

			enable_nonblocking(self.stdout)
			self.watchers[0].set(self.stdout, pyev.EV_READ)
			self.watchers[0].start()

			enable_nonblocking(self.stderr)
			self.watchers[1].set(self.stderr, pyev.EV_READ)
			self.watchers[1].start()

			return pid

		try:
			if self.config['stdin'] == '<null>':
				stdin = os.open(os.devnull, os.O_RDONLY) # Open stdin
			else:
				# Default is to open /dev/null
				stdin = os.open(os.devnull, os.O_RDONLY) # Open stdin

			os.dup2(stdin, 0)
			os.dup2(stdout, 1) # Prepare stdout
			os.dup2(stderr, 2) # Prepare stderr

			# Close all open file descriptors above standard ones.  This prevents the child from keeping
			# open any file descriptors inherited from the parent.
			os.closerange(3, MAXFD)

			try:
				os.execvpe(cmd, args, self.env)
			except Exception, e:
				os.close(1)
				os.write(2, "Execution of command '{1}' failed: {0}\n".format(e, cmd))
				os.close(2)

		finally:
			# No pasaran
			os._exit(3)


	def start(self):
		'''Transition to state STARTING'''
		assert self.state in (program.state_enum.STOPPED, program.state_enum.FATAL)

		L.debug("{0} -> STARTING".format(self))

		if self.log_out_fname is not None:
			self.log_out = open(self.log_out_fname,'a')

		if self.log_err_fname is not None:
			self.log_err = open(self.log_err_fname,'a')

		if self.config['stdout'] == '<stderr>':
			self.log_out = self.log_err
		elif self.config['stderr'] == '<stdout>':
			self.log_err = self.log_out

		self.pid = self.spawn(self.cmdline[0], self.cmdline) #TODO: self.cmdline[0] can be substituted by self.ident or any arbitrary string
		self.state = program.state_enum.STARTING
		self.start_time = time.time()
		self.stop_time = None
		self.term_time = None
		self.launch_cnt += 1


	def stop(self):
		'''Transition to state STOPPING'''
		if self.state == program.state_enum.FATAL: return # This can happen and it is probably OK

		assert self.pid is not None, "Stopping: {0}".format(self)
		assert self.state in (program.state_enum.RUNNING, program.state_enum.STARTING)

		L.debug("{0} -> STOPPING".format(self))
		self.act_stopsignals = self.stopsignals[:]
		signal = self.get_next_stopsignal()
		try:
			os.kill(self.pid, signal)
		except:
			pass
		self.state = program.state_enum.STOPPING
		self.stop_time = time.time()


	def on_terminate(self, status):
		self.term_time = time.time()
		self.pid = None

		# Close process stdout and stderr pipes (including vacuum of actual content)
		self.watchers[0].stop()
		if self.stdout is not None:
			disable_nonblocking(self.stdout)
			while True:
				data = os.read(self.stdout, 4096)
				if len(data) == 0: break
				self.__process_output(self.log_out, 0, data)
			os.close(self.stdout)
			self.stdout = None

		self.watchers[1].stop()
		if self.stderr is not None:
			disable_nonblocking(self.stderr)
			while True:
				data = os.read(self.stderr, 4096)
				if len(data) == 0: break
				self.__process_output(self.log_err, 1, data)
			os.close(self.stderr)
			self.stderr = None

		# Close log files
		if self.log_out is not None:
			self.log_out.close()

		if self.log_err is not None and self.log_out != self.log_err:
			self.log_err.close()

		self.log_out = None
		self.log_err = None

		# Handle state change properly
		if self.state == program.state_enum.STARTING:
			L.warning("{0} exited too quickly (-> FATAL)".format(self))
			self.state = program.state_enum.FATAL

		elif self.state == program.state_enum.STOPPING:
			L.debug("{0} -> STOPPED".format(self))
			self.state = program.state_enum.STOPPED

		else:
			L.warning("{0} exited unexpectedly (-> FATAL)".format(self))
			self.state = program.state_enum.FATAL


	def on_tick(self, now):
		# Switch starting programs into running state
		if self.state == program.state_enum.STARTING:
			if now - self.start_time >= self.config['starttimeout']:
				L.debug("{0} -> RUNNING".format(self))
				self.state = program.state_enum.RUNNING

		elif self.state == program.state_enum.STOPPING:
			if now - self.start_time >= self.config['stoptimeout']:
				L.warning("{0} is still terminating - sending another signal".format(self))
				signal = self.get_next_stopsignal()
				try:
					os.kill(self.pid, signal)
				except:
					pass


	def get_next_stopsignal(self):
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
				os.close(watcher.fd)
				if watcher.data == 0: self.stdout = None
				elif watcher.data == 1: self.stderr = None
				return 

			if watcher.data == 0: self.__process_output(self.log_out, 0, data)
			elif watcher.data == 1: self.__process_output(self.log_err, 1, data)


	def __process_output(self, logf, sourceid, data):
			if logf is not None:
				logf.write(data)
				logf.flush() #TODO: Maybe something more clever here can be better (check logging.StreamHandler)

			# Following code is just example
			if sourceid == 1:
				i = self.kmp.search(data)
				if i >= 0:
					# Pattern detected in the data
					pass

