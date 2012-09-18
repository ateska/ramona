import os, urlparse, socket, struct, time, json, select, logging
###

L = logging.getLogger("cnscom")
Lmy = logging.getLogger("my")

###

callid_ping = 0
callid_start = 1
callid_stop = 2
callid_restart = 3
callid_status = 4
callid_tail = 5

#

call_magic = '>'
resp_magic = '<'

call_struct_fmt = '!cBH'
resp_struct_fmt = '!ccH'

resp_return = 'R'
resp_exception = 'E'
resp_yield_message = 'M' # Used to propagate message from server to console

###

class program_state_enum(object):
	'''Enum'''
	DISABLED = -1
	STOPPED = 0
	STARTING = 10
	RUNNING = 20
	STOPPING = 30
	FATAL = 200
	CFGERROR=201

	labels = {
		DISABLED: 'DISABLED',
		STOPPED: 'STOPPED',
		STARTING: 'STARTING',
		RUNNING: 'RUNNING',
		STOPPING: 'STOPPING',
		FATAL: 'FATAL',
		CFGERROR: 'CFGERROR',
	}


###


def svrcall(cnssocket, callid, params=""):
	'''
	Client side of console communication IPC call (kind of RPC / Remote procedure call).

	@param cnssocket: Socket to server (created by socket_uri factory bellow)
	@param callid: one of callid_* identification
	@param params: string representing parameters that will be passed to server call
	@return: String returned by server or raises exception if server call failed
	'''

	paramlen = len(params)
	if paramlen >= 0x7fff:
		raise RuntimeError("Transmitted parameters are too long.")

	cnssocket.send(struct.pack(call_struct_fmt, call_magic, callid, paramlen)+params)

	while 1:
		x = time.time()
		resp = ""
		while len(resp) < 4:
			rlist, _, _ = select.select([cnssocket],[],[], 5)
			if len(rlist) == 0:
				if time.time() - x > 2: L.error("Looping detected")
				continue
			ndata = cnssocket.recv(4 - len(resp))
			if len(ndata) == 0:
				raise EOFError("It looks like server closed connection")

			resp += ndata

		magic, retype, paramlen = struct.unpack(resp_struct_fmt, resp)
		assert magic == resp_magic

		# Read rest of the response (size given by paramlen)
		params = ""
		while paramlen > 0:
			ndata = cnssocket.recv(paramlen)
			params += ndata
			paramlen -= len(ndata)


		if retype == resp_return:
			# Remote server call returned normally
			return params
		
		elif retype == resp_exception:
			# Remove server call returned exception
			raise RuntimeError(params)
		
		elif retype == resp_yield_message:
			# Remote server call returned yielded message -> we will continue receiving
			obj = json.loads(params)
			obj = logging.makeLogRecord(obj)
			if Lmy.getEffectiveLevel() <= obj.levelno: # Print only if log level allows that
				Lmy.handle(obj)
			continue

		else:
			raise RuntimeError("Unknown server response: {0}".format(retype))

###

class socket_uri(object):
	'''
	Socket factory that is configured using socket URI.
	This is actually quite generic implementation - not specific to console-server IPC communication.
	'''

	# Configure urlparce
	if 'unix' not in urlparse.uses_params: urlparse.uses_params.append('unix')

	def __init__(self, uri):
		self.uri = urlparse.urlparse(uri)
		self.uriparams = dict(urlparse.parse_qsl(self.uri.params))

		self.protocol = self.uri.scheme.lower()
		if self.protocol == 'tcp':
			try:
				_port = self.uri.port
			except ValueError:
				raise RuntimeError("Invalid port number in socket URI {0}".format(uri))

			if self.uri.path != '': raise RuntimeError("Path has to be empty in socket URI {0}".format(uri))

		elif self.protocol == 'unix':
			if self.uri.netloc != '':
				# Special case of situation when netloc is not empty (path is relative)
				self.uri = self.uri._replace(netloc='', path=self.uri.netloc + self.uri.path)

		else:
			raise RuntimeError("Unknown/unsuported protocol '{0}' in socket URI {1}".format(self.protocol, uri))


	def create_socket_listen(self):
		if self.protocol == 'tcp':
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			s.bind((self.uri.hostname, self.uri.port))

		elif self.protocol == 'unix':
			mode = self.uriparams.get('mode',None)
			if mode is None: mode = 0o600
			else: mode = int(mode,8)
			oldmask = os.umask(mode ^ 0o777)
			s = deleteing_unix_socket()
			s.bind(self.uri.path)
			os.umask(oldmask)

		else:
			raise RuntimeError("Unknown/unsuported protocol '{0}'".format(self.protocol))
		
		return s


	def create_socket_connect(self):
		if self.protocol == 'tcp':
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((self.uri.hostname, self.uri.port))

		elif self.protocol == 'unix':
			s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
			s.connect(self.uri.path)

		else:
			raise RuntimeError("Unknown/unsuported protocol '{0}'".format(self.protocol))
		
		return s

###

class deleteing_unix_socket(socket.socket):
	'''
This class is used as wrapper to socket object that represent listening UNIX socket.
It added ability to delete socket file when destroyed.

It is basically used only on server side of UNIX socket.
	'''

	def __init__(self):
		socket.socket.__init__(self, socket.AF_UNIX, socket.SOCK_STREAM)
		self.__sockfile = None


	def __del__(self):
		self.__delsockfile()


	def close(self):
		socket.socket.close(self)
		self.__delsockfile()


	def bind(self, fname):
		socket.socket.bind(self, fname)
		self.__sockfile = fname


	def __delsockfile(self):
		if self.__sockfile is not None:
			fname = self.__sockfile
			self.__sockfile = None
			os.unlink(fname)
			assert not os.path.isfile(fname)


###

def parse_json_kwargs(params):
	'''Used when params are transfered as JSON - it also handles situation when 'params' is empty string '''
	if params == '': return dict()
	return json.loads(params)

###

class svrcall_error(RuntimeError):
	'''
	Exception used to report error to the console without leaving trace in server error log.
	'''
	pass
