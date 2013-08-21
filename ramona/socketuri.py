import os, sys, socket, urlparse

###

class socket_uri(object):
	'''
	Socket factory that is configured using socket URI.
	This is actually quite generic implementation - not specific to console-server IPC communication.
	'''

	# Configure urlparse
	if 'unix' not in urlparse.uses_query: urlparse.uses_query.append('unix')
	if 'tcp' not in urlparse.uses_query: urlparse.uses_query.append('tcp')

	def __init__(self, uri):
		self.uri = urlparse.urlparse(uri.strip())
		self.uriquery = dict(urlparse.parse_qsl(self.uri.query))

		self.protocol = self.uri.scheme.lower()
		if self.protocol == 'tcp':
			try:
				_port = int(self.uri.port)
			except ValueError:
				raise RuntimeError("Invalid port number in socket URI {0}".format(uri))

			if self.uri.path != '': raise RuntimeError("Path has to be empty in socket URI {0}".format(uri))

		elif self.protocol == 'unix':
			if sys.platform == 'win32':
				os.error("UNIX sockets are not supported on this plaform")
				raise RuntimeError("UNIX sockets are not supported on this plaform ({0})".format(uri))
			if self.uri.netloc != '':
				# Special case of situation when netloc is not empty (path is relative)
				self.uri = self.uri._replace(netloc='', path=self.uri.netloc + self.uri.path)

		else:
			raise RuntimeError("Unknown/unsupported protocol '{0}' in socket URI {1}".format(self.protocol, uri))


	def create_socket_listen(self):
		'''Return list of socket created in listen mode.
		The trick here is that for single host/port combinations, multiple listen socket can be created (e.g. IPv4 vs IPv6)
		'''
		retsocks = []

		if self.protocol == 'tcp':
			for family, socktype, proto, canonname, sockaddr in socket.getaddrinfo(self.uri.hostname, self.uri.port, 0, socket.SOCK_STREAM):
				s = socket.socket(family, socktype, proto)
				s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				s.bind(sockaddr)
				retsocks.append(s)

		elif self.protocol == 'unix':
			mode = self.uriquery.get('mode',None)
			if mode is None: mode = 0o600
			else: mode = int(mode,8)
			oldmask = os.umask(mode ^ 0o777)
			s = _deleteing_unix_socket()
			s.bind(self.uri.path)
			os.umask(oldmask)

			retsocks.append(s)

		else:
			raise RuntimeError("Unknown/unsupported protocol '{0}'".format(self.protocol))

		return retsocks


	def create_socket_connect(self):
		if self.protocol == 'tcp':
			last_error = None
			for family, socktype, proto, canonname, sockaddr in socket.getaddrinfo(self.uri.hostname, self.uri.port, 0, socket.SOCK_STREAM):
				try:
					s = socket.socket(family, socktype, proto)
					s.connect(sockaddr)
					return s
				except Exception, e:
					last_error = e
					continue

			# Raise last error from eventual sequence ...
			if last_error is not None: raise last_error
			raise RuntimeError("Unexpected error condition during server connect.")

		elif self.protocol == 'unix':
			s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
			s.connect(self.uri.path)
			return s

		else:
			raise RuntimeError("Unknown/unsuported protocol '{0}'".format(self.protocol))

###

class _deleteing_unix_socket(socket.socket):
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

