import sys, socket, errno, struct, logging, mimetypes
from ..config import config, read_config
from ..utils import socket_uri
from .. import cnscom
import SimpleHTTPServer, BaseHTTPServer, SocketServer
import httplib
import os

###

L = logging.getLogger("httpfendapp")

###

class httpfend_app(object):
	def __init__(self):


		# Prepare server connection factory
#		self.cnsconuri = socket_uri(config.get('console','serveruri'))
		self.ctlconsock = None



	def run(self):
#		if not config.has_section('httpfend'):
#			L.debug("Section [httpfend] does not exist in config. Exiting.")
#			sys.exit(1)
		
#		host = config.get('httpfend', 'host')
#		port = config.get('httpfend', 'host')
		host = "127.0.0.1"
		port = 5588
		# TODO: Missing configuration check
		
		Handler = RamonaHttpReqHandler
		httpd = SocketServer.TCPServer((host, port), Handler)
		L.info("Started HTTP frontend at http://{0}:{1}".format(host, port))
		httpd.serve_forever()


class RamonaHttpReqHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	if not mimetypes.inited:
		mimetypes.init()
	
	def do_GET(self):
		scriptdir = os.path.dirname(os.path.realpath(__file__))
		if self.path.startswith("/static/"):
			parts = self.path.split("/")
			fname = os.path.join(scriptdir, *[x for x in parts if len(x) > 0])
			if not os.path.isfile(fname):
				self.send_error(httplib.NOT_FOUND)
				return
			try:
				f = open(fname, "r")
			except IOError, e:
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
	

if __name__ == '__main__':
	app = httpfend_app()
	app.run()
	