import socket
import signal
import pyev
from .. import socketuri
import logging as L
import select
import collections
import sys
import threading
from BaseHTTPServer import BaseHTTPRequestHandler
import errno
from .app import RamonaHttpReqHandler

class connection(threading.Thread):
	
	def __init__(self, sock, address, server):
		threading.Thread.__init__(self, name="worker")
		self.sock = sock
		self.address = address
		self.server = server
	
	def run(self):
		try:
			handler = RamonaHttpReqHandler(self.sock, self.address, self.server)
		except:
			L.exception("Uncaught exception during worker thread execution:")

class Server(object):
	
	STOPSIGNALS = [signal.SIGINT, signal.SIGTERM]
	NONBLOCKING = frozenset([errno.EAGAIN, errno.EWOULDBLOCK])
	
	def __init__(self):
		self.workers = collections.deque()
		
		# Open console communication sockets (listen mode)
		self.svrsockets = []
#		consoleuri = config.get("ramona:server", "consoleuri")
		consoleuri = "tcp://localhost:8888"
		for cnsuri in consoleuri.split(','):
			socket_factory = socketuri.socket_uri(cnsuri)
			try:
				socks = socket_factory.create_socket_listen()
			except socket.error, e:
				L.fatal("It looks like that server is already running: {0}".format(e))
				sys.exit(1)
			self.svrsockets.extend(socks)
		if len(self.svrsockets) == 0:
			L.fatal("There is no console socket configured - considering this as fatal error")
			sys.exit(1)

		self.loop = pyev.default_loop()
		self.watchers = [pyev.Signal(sig, self.loop, self.__terminal_signal_cb) for sig in self.STOPSIGNALS]
		
		for sock in self.svrsockets:
			sock.setblocking(0)
			self.watchers.append(pyev.Io(sock._sock, pyev.EV_READ, self.loop, self.on_accept))
	
	def run(self):
		
		for sock in self.svrsockets:
			sock.listen(socket.SOMAXCONN)
		for watcher in self.watchers:
			watcher.start()
		
		
		# Launch loop
		try:
			self.loop.start()
		finally:
			for w in self.workers:
#				w.join()
				pass
#				w.terminate


		sys.exit(0)

	def on_accept(self, watcher, events):
		# Fist find relevant socket
		sock = None
		for s in self.svrsockets:
			if s.fileno() == watcher.fd:
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
				worker = connection(clisock, address, self)
				worker.start()
				self.workers.append(worker)

	def __terminal_signal_cb(self, watcher, events):
		watcher.loop.stop()



if __name__ == '__main__':
	srv = Server()
	srv.run()
	
