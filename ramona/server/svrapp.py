import sys, os, socket, signal, errno, weakref, logging, argparse, itertools, time
import pyev
from .. import cnscom
from ..config import config, read_config, config_files, config_includes, get_numeric_loglevel
from ..cnscom import program_state_enum, svrcall_error
from .cnscon import console_connection, message_yield_loghandler, deffered_return
from .proaster import program_roaster
from .idlework import idlework_appmixin
from .svrappsingl import server_app_singleton
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
		os.setpgrp()

		# Parse command line arguments
		parser = argparse.ArgumentParser()
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
		L.debug("Configuration loaded from: {0}".format(', '.join(itertools.chain(config_files,config_includes))))

		# Prepare message yield logger
		my_logger = logging.getLogger('my')
		my_logger.setLevel(logging.DEBUG) 
		my_logger.addHandler(message_yield_loghandler(self))
		my_logger.propagate = False

		# Open console communication socket (listen mode)
		socket_factory = cnscom.socket_uri(config.get("ramona:server", "consoleuri"))
		try:
			self.sock = socket_factory.create_socket_listen()
		except socket.error, e:
			L.fatal("It looks like that server is already running: {0}".format(e))
			sys.exit(1)
		self.sock.setblocking(0)

		self.loop = pyev.default_loop()
		self.watchers = [pyev.Signal(sig, self.loop, self.__terminal_signal_cb) for sig in self.STOPSIGNALS]
		self.watchers.append(pyev.Child(0, False, self.loop, self.__child_signal_cb))
		self.watchers.append(pyev.Io(self.sock._sock, pyev.EV_READ, self.loop, self.__accept_cb))
		self.watchers.append(pyev.Periodic(0, 1.0, self.loop, self.__tick_cb))
		
		self.conns = weakref.WeakSet()
		self.termstatus =  None
		self.termstatus_change = None

		# Enable non-terminating SIGALARM handler
		signal.signal(signal.SIGALRM, _SIGALARM_handler)

		program_roaster.__init__(self)
		idlework_appmixin.__init__(self)

		# Build notificator component
		self.notificator = notificator(self)


	def run(self):
		self.sock.listen(socket.SOMAXCONN)
		for watcher in self.watchers:
			watcher.start()

		# Create pid file
		pidfile = config.get('ramona:server','pidfile')
		if pidfile !='':
			try:
				open(pidfile,'w').write("{0}\n".format(os.getpid()))
			except Exception, e:
				L.critical("Cannot create pidfile: {0}".format(e)) 
				del self.sock # Make sure that socket is explicitly closed (and eventual UNIX socket file deleted)
				sys.exit(1)
				
		# Launch loop
		try:
			self.loop.start()
		finally:
			# Close connections
			for conn in self.conns:
				conn.close()

			# Finalize idle work queue
			self.stop_idlework()

			# Finally remove pid file
			if pidfile !='':
				try:
					os.unlink(pidfile)
				except Exception, e:
					L.error("Cannot remove pidfile: {0}".format(e))
					self.sock.close()
					del self.sock # Make sure that socket is explicitly closed (and eventual UNIX socket file deleted)
					sys.exit(1)

		sys.exit(0)


	def __accept_cb(self, watcher, revents):
		try:
			while True:
				try:
					sock, address = self.sock.accept()
				except socket.error as err:
					if err.args[0] in self.NONBLOCKING:
						break
					else:
						raise
				else:
					if self.termstatus is not None: self.sock.close() # Do not accept new connection when exiting
					if sock.family==socket.AF_UNIX and address=='': address = sock.getsockname()
					conn = console_connection(sock, address, self)
					self.conns.add(conn)

		except:
			L.exception("Exception during server socket accept:")


	def __terminal_signal_cb(self, watcher, _revents):
		if watcher.signum == signal.SIGINT:
			# Print ENTER when Ctrl-C is pressed
			print

		if self.termstatus is None:
			L.info("Exit request received (by signal {0})".format(watcher.signum))
			self.__init_soft_exit()
			return

		else:
			self.__init_real_exit()
			return


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
		self.sock.close()
		while self.watchers:
			self.watchers.pop().stop()


	def dispatch_svrcall(self, cnscon, callid, params):
		if self.termstatus is not None:
			raise cnscom.svrcall_error('Ramona server is exiting - no further commands will be accepted')

		if callid == cnscom.callid_start:
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
			
			return program.tail(**kwargs)

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


def _SIGALARM_handler(signum, frame):
	pass
