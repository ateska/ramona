import socket, errno, struct, weakref, json, select, logging
import pyev
from .. import cnscom
###

L = logging.getLogger("cnscon")

###

class console_connection(object):
	'''Server side of console communication IPC'''

	NONBLOCKING = frozenset([errno.EAGAIN, errno.EWOULDBLOCK])

	def __init__(self, sock, address, serverapp):
		self.serverapp = serverapp

		self.sock = sock
		self.address = address
		self.sock.setblocking(0)
		
		self.read_buf = ""
		self.write_buf = None
		
		self.yield_enabled = False
		self.return_expected = False # This is synchronization element used in asserts preventing IPC goes out of sync

		self.watcher = pyev.Io(self.sock._sock, pyev.EV_READ, serverapp.loop, self.io_cb)
		self.watcher.start()

		L.debug("Console connection open ({0})".format(self.address))


	def __del__(self):
		self.close()


	def reset(self, events):
		self.watcher.stop()
		self.watcher.set(self.sock, events)
		self.watcher.start()


	def io_cb(self, watcher, revents):
		try:
			if (revents & pyev.EV_READ) == pyev.EV_READ:
				self.handle_read()

			if self.sock is None: return # Socket has been just closed

			if (revents & pyev.EV_WRITE) == pyev.EV_WRITE:
				self.handle_write()
		except:
			L.exception("Exception during IO on console connection:")


	def handle_read(self):
		try:
			buf = self.sock.recv(1024)
		except socket.error as err:
			if err.args[0] not in self.NONBLOCKING:
				L.error("Error when reading from console connection socket: {0}".format(err)) 
				self.handle_error()
			return
		
		if len(buf) > 0:
			self.read_buf += buf
			
			while len(self.read_buf) >= 4:
				magic, callid, paramlen = struct.unpack(cnscom.call_struct_fmt, self.read_buf[:4])
				if magic != cnscom.call_magic:
					L.warning("Invalid data stream on control port")
					self.handle_error()
					return

				if (paramlen + 4) <= len(self.read_buf):
					params = self.read_buf[4:4+paramlen]
					self.read_buf = self.read_buf[4+paramlen:]
					
					self.return_expected = True
					try:
						ret = self.serverapp.dispatch_svrcall(self, callid, params)
					except Exception, e:
						if not isinstance(e, cnscom.svrcall_error):
							L.exception("Exception during dispatching console call")
						self.send_exception(e, callid)
					else:
						if ret == deffered_return: return
						self.send_return(ret, callid)

		else:
			L.debug("Connection closed by peer")
			self.handle_error()


	def handle_write(self):
		try:
			sent = self.sock.send(self.write_buf[:select.PIPE_BUF])
		except socket.error as err:
			if err.args[0] not in self.NONBLOCKING:
				#TODO: Log "error writing to {0}".format(self.sock)
				self.handle_error()
				return
		else :
			self.write_buf = self.write_buf[sent:]
			if len(self.write_buf) == 0:
				self.reset(pyev.EV_READ)
				self.write_buf = None


	def write(self, data):
		if self.sock is None:
			L.warning("Socket is closed - write operation is ignored")
			return

		if self.write_buf is None:
			self.write_buf = data
			self.reset(pyev.EV_READ | pyev.EV_WRITE)
		else:
			self.write_buf += data


	def close(self):
		if self.watcher is not None:
			self.watcher.stop()
			self.watcher = None
		if self.sock is not None:
			self.sock.close()
			self.sock = None


	def handle_error(self):
		L.debug("Console connection closed.")
		self.close()


	def send_return(self, ret, callid='-'):
		'''
		Internal function that manages communication of response (type return) to the console (client).
		'''
		assert self.return_expected

		self.yield_enabled = False
		ret = str(ret)
		lenret = len(ret)
		if lenret >= 0x7fff:
			self.handle_error()
			raise RuntimeError("Transmitted return value is too long (callid={0})".format(callid))
		
		self.write(struct.pack(cnscom.resp_struct_fmt, cnscom.resp_magic, cnscom.resp_return, lenret) + ret)
		self.return_expected = False


	def send_exception(self, e, callid='-'):
		'''
		Internal function that manages communication of response (type exception) to the console (client).
		'''
		assert self.return_expected

		self.yield_enabled = False
		ret = str(e)
		lenret = len(ret)
		if lenret >= 0x7fff:
			self.handle_error()
			raise RuntimeError("Transmitted exception is too long (callid={0})".format(callid))
		self.write(struct.pack(cnscom.resp_struct_fmt, cnscom.resp_magic, cnscom.resp_exception, lenret) + ret)
		self.return_expected = False


	def yield_message(self, message):
		if not self.yield_enabled: return
		assert self.return_expected

		messagelen = len(message)
		if messagelen >= 0x7fff:
			raise RuntimeError("Transmitted yield message is too long.")

		self.write(struct.pack(cnscom.resp_struct_fmt, cnscom.resp_magic, cnscom.resp_yield_message, messagelen) + message)

###

class message_yield_loghandler(logging.Handler):
	'''
	Message yield(ing) log handler provides functionality to propagate log messages to connected consoles.
	It automatically emits all log records that are submitted into relevant logger (e.g. Lmy = logging.getLogger("my") ) and forwards them
	as resp_yield_message to connected consoles (yield has to be enabled on particular connection see yield_enabled).
	'''


	def __init__(self, serverapp):
		logging.Handler.__init__(self)
		self.serverapp = weakref.ref(serverapp)


	def emit(self, record):
		serverapp = self.serverapp()
		if serverapp is None: return

		msg = json.dumps({
			'msg': record.msg,
			'args': record.args,
			'funcName': record.funcName,
			'lineno': record.lineno,
			'levelno': record.levelno,
			'levelname': record.levelname,
			'name': record.name,
			'pathname': record.pathname,
		})

		for conn in serverapp.conns:
			conn.yield_message(msg)

###

class deffered_return(object): pass # This is just a symbol definition
