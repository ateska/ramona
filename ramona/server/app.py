import sys, os, socket, signal, errno, weakref, logging, argparse, json
import pyev

from .. import cnscom
from ..config import config, read_config, config_files
from .cnscon import console_connection
from .proaster import program_roaster

from . import call_status

###

L = logging.getLogger("server")

###

class server_app(program_roaster):

	STOPSIGNALS = [signal.SIGINT, signal.SIGTERM]
	NONBLOCKING = frozenset([errno.EAGAIN, errno.EWOULDBLOCK])

	def __init__(self):
		# Create own process group
		os.setpgrp()

		# Parse command line arguments
		parser = argparse.ArgumentParser()
		parser.add_argument('-c', '--config', metavar="CONFIGFILE", action='append', help='Specify config file(s) to read (this option can be given more times).')
		self.args = parser.parse_args()

		# Read configuration
		read_config(self.args.config)

		# Configure logging
		logging.basicConfig(level=logging.DEBUG) #TODO: Improve this ...

		L.debug("Configuration loaded from: {0}".format(':'.join(config_files)))
		
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

		program_roaster.__init__(self)


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
		if watcher.signum == signal.SIGINT: print # Print ENTER when Ctrl-C is pressed
		self.stop()


	def __child_signal_cb(self, watcher, _revents):
		try:
			self.on_terminate_program(watcher.rpid, watcher.rstatus)
		except:
			L.exception("Exception during SIGCHLD callback")


	def __tick_cb(self, watcher, revents):
		try:
			self.on_tick()
		except:
			L.exception("Exception during periodic internal check")


	def stop(self):
		self.loop.stop(pyev.EVBREAK_ALL)
		self.sock.close()
		while self.watchers:
			self.watchers.pop().stop()

		for conn in self.conns:
			conn.close()


	def dispatch_ctrl(self, callid, params):
		if callid == cnscom.callid_start:
			return self.start_program(**json.loads(params))

		elif callid == cnscom.callid_stop:
			return self.stop_program(**json.loads(params))

		elif callid == cnscom.callid_restart:
			return self.restart_program(**json.loads(params))

		elif callid == cnscom.callid_status:
			return call_status.main(self, **json.loads(params))

		else:
			L.error("Received unknown callid: {0}".format(callid))
