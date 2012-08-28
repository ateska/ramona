import socket, errno, struct, logging
import pyev
from .. import cnscom
###

L = logging.getLogger("cnscon")

###

class console_connection(object):
	'''Server side'''

	NONBLOCKING = frozenset([errno.EAGAIN, errno.EWOULDBLOCK])

	def __init__(self, sock, address, serverapp):
		self.serverapp = serverapp

		self.sock = sock
		self.address = address
		self.sock.setblocking(0)
		
		self.read_buf = ""
		self.write_buf = None
		
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
					
					try:
						ret = self.serverapp.dispatch_ctrl(callid, params)
					except Exception, e:
						L.exception("Exception during dispatching console call")
						ret = str(e)
						lenret = len(ret)
						if lenret >= 256*256:
							self.handle_error()
							raise RuntimeError("Transmitted parameters are too long.")
						self.write(struct.pack(cnscom.resp_struct_fmt, cnscom.resp_magic, cnscom.resp_exc, lenret) + ret)						
					else:
						ret = str(ret)
						lenret = len(ret)
						if lenret >= 256*256:
							self.handle_error()
							raise RuntimeError("Transmitted parameters are too long.")
						self.write(struct.pack(cnscom.resp_struct_fmt, cnscom.resp_magic, cnscom.resp_ret, lenret) + ret)

		else:
			L.debug("Connection closed by peer")
			self.handle_error()


	def handle_write(self):
		try:
			sent = self.sock.send(self.write_buf)
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
