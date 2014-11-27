import sys, os, socket, ConfigParser, errno, logging, signal, threading, itertools, collections
import pyev
from ..config import config, read_config, get_numeric_loglevel, config_defaults
from .. import socketuri
from ._request_handler import ramona_http_req_handler

###

L = logging.getLogger("httpfendapp")

###

class httpfend_app(object):

	STOPSIGNALS = [signal.SIGINT, signal.SIGTERM]
	NONBLOCKING = frozenset([errno.EAGAIN, errno.EWOULDBLOCK])
	# Maximum number of worker threads serving the client requests
	MAX_WORKER_THREADS = 10
	
	def __init__(self):
		# Read config
		read_config()
		
		# Configure logging
		try:
			loglvl = get_numeric_loglevel(config.get(os.environ['RAMONA_SECTION'], 'loglevel'))
		except:
			loglvl = logging.INFO
		logging.basicConfig(
			level=loglvl,
			stream=sys.stderr,
			format="%(asctime)s %(levelname)s: %(message)s",
		)

		try:
			self.listenaddr = config.get(os.environ['RAMONA_SECTION'], 'listen')
		except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
			self.listenaddr = config_defaults['ramona:httpfend']['listenaddr']
		
		self.username = None
		self.password = None 
		try:
			self.username = config.get(os.environ['RAMONA_SECTION'], 'username')
			self.password = config.get(os.environ['RAMONA_SECTION'], 'password')
		except:
			pass
		
		if self.username is not None and self.password is None:
			L.fatal("Configuration error: 'username' option is set, but 'password' option is not set. Please set 'password'")
			sys.exit(1)
		
		self.logmsgcnt = itertools.count()
		self.logmsgs = dict()
			
		self.workers = collections.deque()
		self.dyingws = collections.deque() # Dying workers

		self.svrsockets = []
		
		for addr in self.listenaddr.split(','):
			socket_factory = socketuri.socket_uri(addr)
			try:
				socks = socket_factory.create_socket_listen()
			except socket.error, e:
				L.fatal("It looks like that server is already running: {0}".format(e))
				sys.exit(1)
			self.svrsockets.extend(socks)

		if len(self.svrsockets) == 0:
			L.fatal("There is no http server listen address configured - considering this as fatal error")
			sys.exit(1)

		self.loop = pyev.default_loop()
		self.watchers = [
			pyev.Signal(sig, self.loop, self.__terminal_signal_cb) for sig in self.STOPSIGNALS
		]
		self.dyingwas = pyev.Async(self.loop, self.__wdied_cb) # Dying workers async. signaling
		self.watchers.append(self.dyingwas)
		
		for sock in self.svrsockets:
			sock.setblocking(0)
			self.watchers.append(pyev.Io(sock._sock, pyev.EV_READ, self.loop, self.__on_accept, data=sock._sock.fileno()))

		
	def run(self):
		for sock in self.svrsockets:
			sock.listen(socket.SOMAXCONN)
			L.debug("Ramona HTTP frontend is listening at {0}".format(sock.getsockname()))
		for watcher in self.watchers:
			watcher.start()

		L.info('Ramona HTTP frontend started and is available at {0}'.format(self.listenaddr))

		# Launch loop
		try:
			self.loop.start()
		finally:
			# Stop accepting new work
			for sock in self.svrsockets: sock.close()

			# Join threads  ...
			for i in range(len(self.workers)-1,-1,-1):
				w = self.workers[i]
				w.join(2)
				if not w.is_alive(): del self.workers[i]

			if len(self.workers) > 0:
				L.warning("Not all workers threads exited nicely - expect hang during exit")


	def __on_accept(self, watcher, events):
		# First find relevant socket
		sock = None
		for s in self.svrsockets:
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
				clisock.setblocking(1)
				num_workers = len(self.workers)
				if num_workers >= self.MAX_WORKER_THREADS:
					L.error("There are already {0} worker threads, which is >= MAX_WORKER_THREADS = {1}. Not creating a new thread for client {2}".format(
						num_workers, self.MAX_WORKER_THREADS, address))
					continue
				
				worker = _request_worker(clisock, address, self)
				L.debug("Request from client {0} is processed by thread {1}".format(address, worker.name))
				worker.start()
				self.workers.append(worker)
	

	def __terminal_signal_cb(self, watcher, events):
		watcher.loop.stop()


	def __wdied_cb(self, _watcher, _events):
		'''Iterate thru list of workers and remove dead threads'''
		while len(self.dyingws) > 0:
			w = self.dyingws.pop()
			L.debug("Joining thread {0}".format(w.name))
			w.join()
			self.workers.remove(w)

#

class _request_worker(threading.Thread):
	
	def __init__(self, sock, address, server):
		threading.Thread.__init__(self)
		self.name = "HttpfendRequestWorker-{0}".format(self.name)
		self.sock = sock
		self.address = address
		self.server = server
	
	def run(self):
		try:
			ramona_http_req_handler(self.sock, self.address, self.server)
			self.sock.close()
		except:
			L.exception("Uncaught exception during worker thread execution:")
		finally:
			self.server.dyingws.append(self)
			self.server.dyingwas.send()

