import os, urlparse, socket, struct, time, json, logging
###

L = logging.getLogger("cnscom")

###

callid_start = 1
callid_stop = 2
callid_restart = 3
callid_status = 4

#

call_magic = '>'
resp_magic = '<'

call_struct_fmt = '!cBH'
resp_struct_fmt = '!ccH'

resp_ret = 'R'
resp_exc = 'E'

###

class program_state_enum(object):
	'''Enum'''
	STOPPED = 0
	STARTING = 10
	RUNNING = 20
	STOPPING = 30
	FATAL = 200
	CFGERROR=201

	labels = {
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
	
	x = time.time()
	resp = ""
	while len(resp) < 4:
		resp += cnssocket.recv(4 - len(resp))
		if len(resp) == 0:
			if time.time() - x > 2:
				L.error("Looping detected")
				time.sleep(5)

	magic, retype, paramlen = struct.unpack(resp_struct_fmt, resp)
	assert magic == resp_magic
	params = cnssocket.recv(paramlen)
	
	if retype == resp_ret:
		# Remote server call returned normally
		return params
	
	elif retype == resp_exc:
		# Remove server call returned exception
		raise RuntimeError(params)
	
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
			pass

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
		if self.__sockfile is not None:
			fname = self.__sockfile
			self.__sockfile = None
			os.unlink(fname)
			assert not os.path.isfile(fname)


	def bind(self, fname):
		socket.socket.bind(self, fname)
		self.__sockfile = fname

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
