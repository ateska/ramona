import sys, socket, errno, struct, logging, mimetypes
from ..config import config, read_config
from .. import cnscom
import SimpleHTTPServer, BaseHTTPServer, SocketServer
import httplib
import os
import ConfigParser

###

L = logging.getLogger("httpfendapp")

###

# Initialize mimetypes
if not mimetypes.inited:
		mimetypes.init()


class httpfend_app(object):
	def __init__(self):

		# Read config
		read_config()

		print "Config done"
		# Configure logging
		logging.basicConfig(
			level=logging.INFO,
			stream=sys.stderr,
			format="%(levelname)s: %(message)s"
		)

		# Prepare server connection factory
#		self.cnsconuri = cnscom.socket_uri(config.get('ramona:console','serveruri'))
		print "Done with init"
		


	def run(self):
		try:
			host = config.get(os.environ['RAMONA_SECTION'], 'host')
			port = config.getint(os.environ['RAMONA_SECTION'], 'port')
		except ConfigParser.NoSectionError, e:
			L.fatal("Missing configuration section {0}. Exiting.".format(os.environ['RAMONA_SECTION']))
			sys.exit(1)
		except ConfigParser.NoOptionError, e:
			L.fatal("Missing configuration option: {0}. Exiting".format(e))
			sys.exit(1)
		
		Handler = RamonaHttpReqHandler
		httpd = SocketServer.TCPServer((host, port), Handler)
		L.info("Started HTTP frontend at http://{0}:{1}".format(host, port))
		httpd.serve_forever()


class RamonaHttpReqHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	
	def do_GET(self):
		scriptdir = os.path.join(".", "ramona", "httpfend")
		if self.path.startswith("/static/"):
			parts = self.path.split("/")
			fname = os.path.join(scriptdir, *[x for x in parts if len(x) > 0])
			if not os.path.isfile(fname):
				self.send_error(httplib.NOT_FOUND)
				return
			try:
				f = open(fname, "r")
			except IOError:
				self.send_error(httplib.NOT_FOUND)
				return
			with f:
				self.send_response(httplib.OK)
				self.send_header("Content-Type", mimetypes.guess_type(self.path)[0])
				self.end_headers()
				self.wfile.write(f.read())
		elif self.path == "/":
			self.send_response(httplib.OK)
			self.send_header("Content-Type", mimetypes.guess_type(self.path))
			self.end_headers()
			with open(os.path.join(scriptdir, "index.tmpl.html")) as f:
				self.wfile.write(f.read().format())
		else:
			self.send_error(httplib.NOT_FOUND)
	
