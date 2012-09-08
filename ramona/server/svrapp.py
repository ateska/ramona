import sys, os, socket, signal, errno, weakref, logging, argparse, itertools
import pyev
from .. import cnscom
from ..config import config, read_config, config_files, config_includes, get_numeric_loglevel
from .cnscon import console_connection, message_yield_loghandler
from .proaster import program_roaster
from .idlework import idlework_appmixin

from . import call_status

###

L = logging.getLogger("server")

###

class server_app(program_roaster, idlework_appmixin):

	STOPSIGNALS = [signal.SIGINT, signal.SIGTERM]
	NONBLOCKING = frozenset([errno.EAGAIN, errno.EWOULDBLOCK])

	def __init__(self):

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
			format="%(levelname)s: %(message)s"
			)
		# Prepare message yield logger
		my_logger = logging.getLogger('my')
		my_logger.setLevel(logging.DEBUG) 
		my_logger.addHandler(message_yield_loghandler(self))
		my_logger.propagate = False

		L.debug("Configuration loaded from: {0}".format(', '.join(itertools.chain(config_files,config_includes))))
		
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

		# Enable non-terminating SIGALARM handler
		signal.signal(signal.SIGALRM, _SIGALARM_handler)

		program_roaster.__init__(self)
		idlework_appmixin.__init__(self)


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
			self.__init_soft_exit() # Soft
			return

		elif self.termstatus ==  1:
			self.termstatus =  2 # Hard
			self.stop_loop()


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


	def dispatch_svrcall(self, callid, params):
		if self.termstatus is not None:
			raise cnscom.svrcall_error('Ramona server is exiting - no further commands will be accepted')

		self.add_idlework(self.on_tick) # Schedule extra periodic check (to provide swift server background response to to user action)

		if callid == cnscom.callid_start:
			return self.start_program(**cnscom.parse_json_kwargs(params))

		elif callid == cnscom.callid_stop:
			kwargs = cnscom.parse_json_kwargs(params)
			mode = kwargs.pop('mode',None)
			if mode is None or mode == 'stay':
				return self.stop_program(**kwargs)
			elif mode == 'exit':
				return self.__init_soft_exit()
			else:
				L.warning("Unknown exit mode issued: {0}".format(mode))

		elif callid == cnscom.callid_restart:
			return self.restart_program(**cnscom.parse_json_kwargs(params))

		elif callid == cnscom.callid_status:
			return call_status.main(self, **cnscom.parse_json_kwargs(params))

		elif callid == cnscom.callid_ping:
			return params

		else:
			L.error("Received unknown callid: {0}".format(callid))


	def __init_soft_exit(self):
		if self.termstatus > 1: return

		self.termstatus =  1
		self.stop_program(force=True)
		self.add_idlework(self.on_tick) # Schedule extra periodic check 



def _SIGALARM_handler(signum, frame):
	pass
