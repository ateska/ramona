import socket
import signal
import pyev
from .. import socketuri
import logging as L
import select

class connection(object):
	def start(self, sock, address, serverapp):
		self.msg = "HTTP/1.0 200 OK\r\nContent-Length: 5\r\n\r\nPong!\r\n"
		self.sock = sock
		self.sock.setblocking(0)
		self.write = self.write_msg
		self.writewatcher = pyev.Io(self.sock, pyev.EV_WRITE, serverapp.loop, self.write)
		self.writewatcher.start()

	
#	def io_cb(self, watcher, revents):
#		try:
#			if (revents & pyev.EV_READ) == pyev.EV_READ:
#				self.handle_read()
#
#			if self.sock is None: return # Socket has been just closed
#
#			if (revents & pyev.EV_WRITE) == pyev.EV_WRITE:
#				self.handle_write()
#		except:
#			L.exception("Exception during IO on console connection:")
#
#
#	def handle_write(self):
#		try:
#			sent = self.sock.send(self.write_buf[:select.PIPE_BUF])
#		except socket.error as err:
#			if err.args[0] not in self.NONBLOCKING:
#				#TODO: Log "error writing to {0}".format(self.sock)
#				self.handle_error()
#				return
#		else :
#			self.write_buf = self.write_buf[sent:]
#			if len(self.write_buf) == 0:
#				self.reset(pyev.EV_READ)
#				self.write_buf = None


	def write_msg(self, watcher, events):
		self.sock.send(self.msg)
		self.writewatcher.stop()
		self.sock.close()

class Server(object):
	def start(self, loop):
		self.loop = loop
		socket_factory = socketuri.socket_uri("tcp://localhost:9999")
		self.socks = socket_factory.create_socket_listen()
		
#		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#		self.sock.bind(('localhost', 10000))
#		self.sock.listen(500)
#		self.watchers.append(pyev.Io(sock._sock, pyev.EV_READ, self.loop, self.__accept_cb))
		self.acceptwatchers = []
		for sock in self.socks:
			sock.setblocking(0)
			self.acceptwatchers.append(pyev.Io(sock._sock, pyev.EV_READ, self.loop, self.accept))
			sock.listen(socket.SOMAXCONN)
		for watcher in self.acceptwatchers:
			watcher.start()
#		self.acceptwatcher = pyev.Io(self.sock._sock, pyev.EV_READ, loop, self.accept)
#		self.acceptwatcher.start()

	def accept(self, watcher, events):
		# Fist find relevant socket
		sock = None
		for s in self.socks:
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
#				if self.termstatus is not None: clisock.close() # Do not accept new connection when exiting
				if clisock.family==socket.AF_UNIX and address=='': address = clisock.getsockname()
				conn = connection(clisock, address, self)
#				self.conns.add(conn)

#		print "Serving event", events, "with socket", sock
#		client = Client()
#		client.start(watcher.loop, sock)

def interrupt(watcher, events):
	watcher.loop.stop()

loop = pyev.default_loop()
sigwatch = pyev.Signal(signal.SIGINT, loop, interrupt)
sigwatch.start()
srv = Server()
srv.start(loop)
loop.start()
