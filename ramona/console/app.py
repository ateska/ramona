import sys, socket, errno, logging, time
from ..config import config, read_config
from ..utils import launch_server_daemonized
from .. import cnscom
from .parser import argparser
from . import exception

###

L = logging.getLogger("cnsapp")

###

class console_app(object):
	'''
Console application (base for custom implementations)
	'''

	def __init__(self):
		self.argparser = argparser()

		if (len(sys.argv) < 2):
			# Default command
			argv = ['console']
		else:
			argv = None

		self.argparser.parse(argv)

		# Read config
		read_config(self.argparser.args.config)

		# Configure logging
		llvl = logging.INFO
		if self.argparser.args.silent: llvl = logging.ERROR
		if self.argparser.args.debug: llvl = logging.DEBUG
		logging.basicConfig(
			level=llvl,
			stream=sys.stderr,
			format="%(levelname)s: %(message)s"
		)
		if self.argparser.args.debug:
			L.debug("Debug output is enabled.")

		# Prepare server connection factory
		self.cnsconuri = cnscom.socket_uri(config.get('ramona:console','serveruri'))
		self.ctlconsock = None


	def run(self):
		try:
			ec = self.argparser.execute(self)
		except exception.ramona_runtime_errorbase, e:
			L.error("{0}".format(e))
			ec = e.exitcode
		except Exception, e:
			L.error("{0}".format(e))
			ec = 100 # Generic error exit code
		sys.exit(ec if ec is not None else 0)


	def connect(self):
		if self.ctlconsock is None: 
			try:
				self.ctlconsock = self.cnsconuri.create_socket_connect()
			except socket.error, e:
				if e.errno == errno.ECONNREFUSED: return None
				if e.errno == errno.ENOENT and self.cnsconuri.protocol == 'unix': return None
				raise

		return self.ctlconsock


	def svrcall(self, callid, params="", auto_connect=False, auto_server_start=False):
		'''
		@param auto_connect: Automatically establish server connection if not present
		@param auto_server_start: Automatically start server if not running and establish connection
		'''
		assert not (auto_connect & auto_server_start), "Only one of auto_connect and auto_server_start can be true"
		if auto_connect:
			if self.ctlconsock is None:
				s = self.connect()
				if s is None:
					raise exception.server_not_responding_error("Server is not responding - maybe it isn't running.")

		elif auto_server_start:
			# Fist check if ramona server is running and if not, launch that
			s = self.connect()
			if s is None:
				L.debug("It looks like Ramona server is not running - launching server")
				launch_server_daemonized()

				for _ in range(100): # Check server availability for next 10 seconds 
					# TODO: Also improve 'crash-start' detection (to reduce lag when server fails to start)
					time.sleep(0.1)
					s = self.connect()
					if s is not None: break

			if s is None:
				raise exception.server_start_error("Ramona server process start failed")

		else:
			assert self.ctlconsock is not None

		try:
			return cnscom.svrcall(self.ctlconsock, callid, params)
		except socket.error:
			pass

		if auto_connect or auto_server_start:
			L.debug("Reconnecting to server ...")

			self.ctlconsock = None
			s = self.connect()
			if s is None:
				raise exception.server_not_responding_error("Server is not responding - maybe it isn't running.")

			return cnscom.svrcall(self.ctlconsock, callid, params)
