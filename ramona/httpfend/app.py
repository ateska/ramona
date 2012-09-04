import sys, socket, errno, struct, logging, mimetypes, json
from ..config import config, read_config
from .. import cnscom
import BaseHTTPServer
import httplib
import os
import ConfigParser
import time
from ..cnscom import program_state_enum
import cgi
import pprint

###

L = logging.getLogger("httpfendapp")

###

# Initialize mimetypes
if not mimetypes.inited:
		mimetypes.init()

cnsconuri = None

class httpfend_app(object):
	def __init__(self):

		# Read config
		read_config()

		# Configure logging
		logging.basicConfig(
			level=logging.DEBUG,
			stream=sys.stderr,
			format="%(levelname)s: %(message)s"
		)

		# Prepare server connection factory
		global cnsconuri
		cnsconuri = cnscom.socket_uri(config.get('ramona:console','serveruri'))
		


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
		httpd = BaseHTTPServer.HTTPServer((host, port), Handler)
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
				conn = self.socket_connect()
				status = cnscom.svrcall(conn, cnscom.callid_status, json.dumps({}))
				L.debug("Statuses" + status)
				sttable = self.buildStatusTable(json.loads(status))
				L.debug("Status table" + sttable)
				html = f.read().format(statuses=sttable)
				L.debug("HTML" + html)
				self.wfile.write(html)
				
		else:
			self.send_error(httplib.NOT_FOUND)
			
			
	def buildStatusTable(self, statuses):
		ret = '<table class="table table-hover table-bordered"><thead>'
		ret += '<tr><th>Name</th><th>Status</th><th>PID</th><th>Launches</th><th>Start time</th><th>Terminate time</th><th></th></tr>'
		ret += "</thead>"
		ret += "<tbody>"
		for sp in statuses:

			ret += "<tr>"
			
			ret += '<th>{0}</th>'.format(sp.pop('ident', '???'))
			labelCls = "label-inverse"
			progState = sp.pop("state")
			
			if progState == program_state_enum.RUNNING:
				labelCls = "label-success"
			elif progState == program_state_enum.STOPPED:
				labelCls = ""
			elif progState in (program_state_enum.STOPPING, program_state_enum.STARTING):
				labelCls = "label-info"
			elif progState == program_state_enum.STOPPED:
				labelCls = ""
			elif progState in (program_state_enum.FATAL, program_state_enum.CFGERROR):
				labelCls = "label-important"
			
			
			ret += '<td><span class="label {0}">{1}</span></td>'.format(labelCls, cgi.escape(sp.pop('stlbl', '???')))
			ret += '<td>{0}</td>'.format(sp.pop('pid', ""))
			ret += '<td>{0}</td>'.format(sp.pop('launch_cnt', ""))
			t = sp.pop('start_time')
			tform = ""
			if t is not None: tform = time.strftime("%d-%m-%Y %H:%M:%S",time.localtime(t))
			ret += '<td>{0}</td>'.format(tform)
			t = sp.pop('term_time')
			tform = ""
			if t is not None: tform = time.strftime("%d-%m-%Y %H:%M:%S",time.localtime(t))
			ret += '<td>{0}</td>'.format(tform)
			
			actions = ['<a class="btn btn-small btn-success" href="">Start</a>',
				    '<a class="btn btn-small btn-danged" href="">Stop</a>',
				    '<a class="btn btn-small btn-warning" href="">Restart</a>']
			if progState == program_state_enum.FATAL:
				actions.append('<a class="btn btn-small btn-danged" href="">Start (force)</a>')
			ret += '<td>{0}</td>'.format(" ".join(actions))
			
			ret += "</tr>"
			
			if len(sp) > 0:
				ret += '<tr class="info"><td colspan="2"></td><td colspan="5"><pre class="pre-scrollable">'
				ret += cgi.escape(pprint.pformat(sp, width=3))
				print '</pre></td></tr>'
		
		ret += "</tbody></table>"
		
		return ret

	
	def socket_connect(self):
		try:
			return cnsconuri.create_socket_connect()
		except socket.error, e:
			if e.errno == errno.ECONNREFUSED: return None
			if e.errno == errno.ENOENT and self.cnsconuri.protocol == 'unix': return None
			raise


	
