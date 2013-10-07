import sys, os, socket, signal, errno, weakref, logging, argparse, itertools, time, json
import pyev
from .. import cnscom, socketuri, version as ramona_version
from ..config import config, read_config, config_files, config_includes, get_numeric_loglevel, get_logconfig
from ..cnscom import program_state_enum, svrcall_error
from ..utils import rotate_logfiles
from .cnscon import console_connection, message_yield_loghandler, deffered_return
from .proaster import program_roaster
from .idlework import idlework_appmixin
from .singleton import server_app_singleton
from .notify import notificator

from . import call_status

###

L = logging.getLogger("server")

###

class server_app(program_roaster, idlework_appmixin, server_app_singleton):

	STOPSIGNALS = [signal.SIGINT, signal.SIGTERM]
	NONBLOCKING = frozenset([errno.EAGAIN, errno.EWOULDBLOCK])

	def __init__(self):
		server_app_singleton.__init__(self)

		# Create own process group
		if os.name == 'posix':
			os.setpgrp()

		# Parse command line arguments
		parser = argparse.ArgumentParser()
		parser.add_argument('-S','--server-only', action='store_true', help='Start only server, programs are not launched')
		parser.add_argument('program', nargs='*', help='Optionally specify program(s) in scope of the command (if nothing is specified, all enabled programs will be launched)')

		# This is to support debuging of pythonservice.exe on Windows
		if sys.platform == 'win32':
			parser.add_argument('-debug', action='store', help=argparse.SUPPRESS)

		self.args = parser.parse_args()

		# Read configuration
		read_config()

		# Configure logging
		loglvl = get_numeric_loglevel(config.get('ramona:server','loglevel'))
		logging.basicConfig(
			level=loglvl,
			stream=sys.stderr,
			format="%(asctime)s %(levelname)s: %(message)s",
			)
		L.info("Ramona server started")
		L.debug("Configuration loaded from: {0}".format(', '.join(itertools.chain(config_files,config_includes))))

		# Prepare message yield logger
		my_logger = logging.getLogger('my')
		my_logger.setLevel(logging.DEBUG) 
		my_logger.addHandler(message_yield_loghandler(self))
		my_logger.propagate = False

		# Open console communication sockets (listen mode)
		self.cnssockets = []
		consoleuri = config.get("ramona:server", "consoleuri")
		for cnsuri in consoleuri.split(','):
			socket_factory = socketuri.socket_uri(cnsuri)
			
			# Special casing for UNIX domain socket 
			# There can be abandoned/stalled file entry - we need to find out if this is the case ...
			# (see http://stackoverflow.com/questions/7405932/how-to-know-whether-any-process-is-bound-to-a-unix-domain-socket)
			if socket_factory.protocol == 'unix':
				# Try to connect ...
				if os.path.exists(socket_factory.uri.path):
					try:
						s = socket_factory.create_socket_connect()
					except socket.error, e:
						if e.errno == errno.ECONNREFUSED:
							L.debug("Removing stalled UNIX socket '{0}'".format(socket_factory.uri.path))
							os.unlink(socket_factory.uri.path)
					else:
						s.close()
						L.fatal("It looks like that server is already running, there is active UNIX socket '{0}'".format(socket_factory.uri.path))
						sys.exit(1)

			try:
				socks = socket_factory.create_socket_listen()
			except socket.error, e:
				L.fatal("It looks like that server is already running: {0}".format(e))
				sys.exit(1)
			self.cnssockets.extend(socks)
		if len(self.cnssockets) == 0:
			L.fatal("There is no console socket configured - considering this as fatal error")
			sys.exit(1)

		self.loop = pyev.default_loop()
		self.watchers = [pyev.Signal(sig, self.loop, self.__terminal_signal_cb) for sig in self.STOPSIGNALS]
		self.watchers.append(pyev.Periodic(0, 1.0, self.loop, self.__tick_cb))

		if sys.platform == 'win32':
			# There is no pyev.Child watcher on Windows; periodic check is used instead
			self.watchers.append(pyev.Periodic(0, 0.5, self.loop, self.__check_childs_cb))
		else:
			self.watchers.append(pyev.Child(0, False, self.loop, self.__child_signal_cb))


		for sock in self.cnssockets:
			sock.setblocking(0)
			# Watcher data are used (instead logical watcher.fd due to Win32 mismatch)
			self.watchers.append(pyev.Io(sock._sock, pyev.EV_READ, self.loop, self.__accept_cb, data=sock._sock.fileno()))

		self.conns = weakref.WeakSet()
		self.termstatus =  None
		self.termstatus_change = None

		# Enable non-terminating SIGALARM handler
		if sys.platform != 'win32':
			signal.signal(signal.SIGALRM, _SIGALARM_handler)

		# Prepare also exit watcher - can be used to 'simulate' terminal signal (useful on Win32)
		self.exitwatcher = pyev.Async(self.loop, self.__terminal_signal_cb)
		self.exitwatcher.start()

		program_roaster.__init__(self)
		idlework_appmixin.__init__(self)

		# Build notificator component
		self.notificator = notificator(self)

		# Reopen stdout and stderr - if pointing to log file, this includes also log rotate check
		self.__rotate_stdout_stderr()


	def run(self):
		for sock in self.cnssockets:
			sock.listen(socket.SOMAXCONN)
		for watcher in self.watchers:
			watcher.start()

		# Create pid file
		pidfile = config.get('ramona:server','pidfile')
		if pidfile !='':
			pidfile = os.path.expandvars(pidfile)
			try:
				open(pidfile,'w').write("{0}\n".format(os.getpid()))
			except Exception, e:
				L.critical("Cannot create pidfile: {0}".format(e)) 
				del self.cnssockets # Make sure that socket is explicitly closed (and eventual UNIX socket file deleted)
				sys.exit(1)

		# Launch start sequence
		if not self.args.server_only:
			self.start_program(pfilter=self.args.program if len(self.args.program) > 0 else None)

		# Start heartbeat loop
		try:
			self.loop.start()
		finally:
			# Close connections
			for conn in self.conns:
				conn.close()

			# Finalize idle work queue
			self.stop_idlework()

			# Go thru final tick at notificator (this will ensure final persistance of a stash)
			self.notificator.on_tick(time.time())

			# Finally remove pid file
			if pidfile !='':
				try:
					os.unlink(pidfile)
				except Exception, e:
					L.error("Cannot remove pidfile: {0}".format(e))
					while len(self.cnssockets) > 0:
						sock = self.cnssockets.pop()
						sock.close()
						del sock # Make sure that socket is explicitly closed (and eventual UNIX socket file deleted)
					sys.exit(1)

		sys.exit(0)


	def __accept_cb(self, watcher, revents):
		'''Accept incomming console connection'''
		try:
			# Fist find relevant socket
			sock = None
			for s in self.cnssockets:
				if s.fileno() == watcher.data:
					sock = s
					break

			if sock is None:
				L.warning("Received accept request on unknown socket {0}".format(watcher.fd))
				return

			# Accept all connection that are pending in listen backlog
			while True:
				try:
					clisock, address = sock.accept()
				except socket.error as err:
					if err.args[0] in self.NONBLOCKING:
						break
					else:
						raise
				else:
					if self.termstatus is not None: clisock.close() # Do not accept new connection when exiting
					if sys.platform != 'win32' and clisock.family==socket.AF_UNIX and address=='': address = clisock.getsockname()
					conn = console_connection(clisock, address, self)
					self.conns.add(conn)

		except:
			L.exception("Exception during server socket accept:")


	def __terminal_signal_cb(self, watcher, _revents):
		if hasattr(watcher, 'signum'):
			if watcher.signum == signal.SIGINT:
				# Print ENTER when Ctrl-C is pressed
				print

		if self.termstatus is None:
			if hasattr(watcher, 'signum'):
				L.info("Exit request received (by signal {0})".format(watcher.signum))
			else:
				L.info("Exit request received")
			self.__init_soft_exit()
			return

		else:
			self.__init_real_exit()
			return


	def __check_childs_cb(self, watcher, _revents):
		'''This is alternative way of detecting subprocess exit - used on Windows'''
		extra_tick = False
		for p in self.roaster:
			if p.subproc is None: continue
			ret = p.subproc.poll()
			if ret != None:
				self.on_terminate_program(p.subproc.pid, ret)
				extra_tick = True

			if p.subproc is not None:
				p.win32_read_stdfd()	


		if extra_tick:
			self.add_idlework(self.on_tick)



	def __child_signal_cb(self, watcher, _revents):
		try:
			self.on_terminate_program(watcher.rpid, watcher.rstatus)
			self.add_idlework(self.on_tick) # Schedule extra periodic check 
		except:
			L.exception("Exception during SIGCHLD callback")


	def __tick_cb(self, watcher, revents):
		try:
			self.on_tick()
		except:
			L.exception("Exception during periodic internal check")


	def stop_loop(self):
		'''
		Stop internal loop and exit.
		'''
		self.loop.stop(pyev.EVBREAK_ALL)
		for sock in self.cnssockets:
			sock.close()
		while self.watchers:
			self.watchers.pop().stop()


	def dispatch_svrcall(self, cnscon, callid, params):
		if self.termstatus is not None:
			raise cnscom.svrcall_error('Ramona server is exiting - no further commands will be accepted')
			
		if callid == cnscom.callid_init:
			return json.dumps({"version": ramona_version})
			
		elif callid == cnscom.callid_start:
			kwargs = cnscom.parse_json_kwargs(params)
			immediate = kwargs.pop('immediate', False)
			if immediate:
				return self.start_program(cnscon=None, **kwargs)
			else:
				cnscon.yield_enabled=True
				self.start_program(cnscon=cnscon, **kwargs)
				return deffered_return


		elif callid == cnscom.callid_stop:
			kwargs = cnscom.parse_json_kwargs(params)
			immediate = kwargs.pop('immediate', False)
			mode = kwargs.pop('mode',None)

			if mode is None or mode == 'stay':
				self.add_idlework(self.on_tick) # Schedule extra periodic check (to provide swift server background response to to user action)
				if immediate:
					return self.stop_program(cnscon=None, **kwargs)
				else:
					cnscon.yield_enabled=True
					self.stop_program(cnscon=cnscon, **kwargs)
					return deffered_return

			elif mode == 'exit':
				if immediate:
					return self.__init_soft_exit(cnscon=None, **kwargs)
				else:
					cnscon.yield_enabled=True
					self.__init_soft_exit(cnscon=cnscon, **kwargs)
					return deffered_return

			else:
				L.warning("Unknown exit mode issued: {0}".format(mode))

		elif callid == cnscom.callid_restart:
			self.add_idlework(self.on_tick) # Schedule extra periodic check (to provide swift server background response to to user action)
			kwargs = cnscom.parse_json_kwargs(params)
			immediate = kwargs.pop('immediate', False)
			if immediate:
				return self.restart_program(cnscon=None, **kwargs)
			else:
				cnscon.yield_enabled=True
				self.restart_program(cnscon=cnscon, **kwargs)
				return deffered_return

		elif callid == cnscom.callid_status:
			return call_status.main(self, **cnscom.parse_json_kwargs(params))

		elif callid == cnscom.callid_ping:
			return params

		elif callid == cnscom.callid_tail:
			kwargs = cnscom.parse_json_kwargs(params)
			program = kwargs.pop('program')
			try:
				program = self.get_program(program)
			except KeyError, e:
				raise svrcall_error("{0}".format(e.message))
			
			return program.tail(cnscon, **kwargs)

		elif callid == cnscom.callid_tailf_stop:
			kwargs = cnscom.parse_json_kwargs(params)
			program = kwargs.pop('program')
			try:
				program = self.get_program(program)
			except KeyError, e:
				raise svrcall_error("{0}".format(e.message))
			
			return program.tailf_stop(cnscon, **kwargs)

		elif callid == cnscom.callid_who:
			ret = []
			for c in self.conns:
				ret.append({
					"me": cnscon == c,
					"descr": c.descr,
					"address": c.address,
					"connected_at": c.connected_at
				})
			return json.dumps(ret)


		elif callid == cnscom.callid_notify:
			kwargs = cnscom.parse_json_kwargs(params)
			t = kwargs['text']
			if len(t) > 0:
				self.notificator.publish(kwargs['target'], t, kwargs['subject'])
			else:
				self.notificator.send_daily(None, None)
			return "OK"

		else:
			L.error("Received unknown callid: {0}".format(callid))


	def on_tick(self):
		now = time.time()
		program_roaster.on_tick(self, now)

		# If termination status take too long - do hard kill
		if self.termstatus_change is not None:
			if (now - self.termstatus_change) > 5:
				if self.termstatus != 3:
					self.__init_real_exit()
				else:
					L.fatal("It looks like server shutdown is taking way too much time - taking nasty exit")
					os._exit(10) 

		if (self.termstatus == 1) and (self.stop_seq is None):
			# Special care for server terminating condition 
			not_running_states=frozenset([program_state_enum.STOPPED, program_state_enum.FATAL, program_state_enum.CFGERROR, program_state_enum.DISABLED])
			ready_to_stop = True
			for p in self.roaster: # Seek for running programs
				if p.state not in not_running_states:
					ready_to_stop = False
					break

			if ready_to_stop: # Happy-flow (stop sequence finished and there is no program running - we can stop looping and exit)
				for p in self.roaster:
					if p.state in (program_state_enum.FATAL, program_state_enum.CFGERROR):
						L.warning("Process in error condition during exit: {0}".format(p))

				self.__init_soft2_exit(self)
			else:
				L.warning("Restarting stop sequence due to exit request.")
				self.stop_program(force=True)

		if (self.termstatus == 2):
			self.__close_idle_conns()
			if len(self.conns) == 0:
				self.__init_real_exit()

		#Ensure stash persistence
		self.notificator.on_tick(now)

		#Evaluate if Ramona log needs to be rotated
		self.__rotate_stdout_stderr()


	def __init_soft_exit(self, cnscon=None, **kwargs):
		if self.termstatus > 1: return

		self.termstatus =  1
		self.termstatus_change = time.time()
		self.stop_program(cnscon=cnscon, force=True, **kwargs)
		self.add_idlework(self.on_tick) # Schedule extra periodic check 


	def __init_soft2_exit(self, cnscon=None):
		'''Term status 2: Clean idling console connections and wait for others console connections to close'''
		if self.termstatus > 2: return
		if self.termstatus == 1: self.__close_idle_conns()
		self.termstatus = 2
		self.termstatus_change = time.time()


	def __init_real_exit(self):
		self.termstatus = 3
		self.termstatus_change = time.time()
		self.stop_loop()


	def __close_idle_conns(self):
		for conn in list(self.conns):
			if conn.write_buf is None \
			   and len(conn.read_buf) == 0 \
			   and conn.yield_enabled is False \
			   and conn.return_expected is False:
				conn.close()


	def __rotate_stdout_stderr(self):
		'''
		Conditionally check if we need to rotate log file of Ramona server
		'''

		logfile = os.environ.get('RAMONA_LOGFILE')
		if logfile is None: return # There is no file to rotate ...

		logfstat = os.fstat(sys.stderr.fileno())
		logbackups, logmaxsize, logcompress = get_logconfig()

		if logfstat.st_size < logmaxsize:
			# Not rotating ...
			return

		try:
			rotate_logfiles(self, logfile, logbackups, logcompress)
		finally:
			# Reopen log file and attach that to stdout and stderr
			w = os.open(logfile, os.O_WRONLY | os.O_APPEND |os.O_CREAT)
			os.dup2(w, 1)
			os.dup2(w, 2)
			os.close(w)


def _SIGALARM_handler(signum, frame):
	pass
