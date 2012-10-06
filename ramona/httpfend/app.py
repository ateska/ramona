import sys, os, socket, ConfigParser, errno, logging, httplib, BaseHTTPServer, mimetypes, json, signal
import time, cgi, pprint, urllib, urlparse, itertools, base64, hashlib
from ..config import config, read_config, get_numeric_loglevel
from .. import cnscom

###

L = logging.getLogger("httpfendapp")

###

STRFTIME_FMT = "%d-%b-%Y %H:%M:%S"

###

# Initialize mimetypes
if not mimetypes.inited:
		mimetypes.init()

###

class httpfend_app(object):

	instance = None

	def __init__(self):
		assert self.instance is None
		httpfend_app.instance = self
		
		# Read config
		read_config()
		
		# Configure logging
		try:
			loglvl = get_numeric_loglevel(config.get(os.environ['RAMONA_SECTION'], 'loglevel'))
		except:
			loglvl = logging.INFO
		logging.basicConfig(
			level=loglvl,
			stream=sys.stderr,
			format="%(asctime)s %(levelname)s: %(message)s",
		)

		try:
			host = config.get(os.environ['RAMONA_SECTION'], 'host')
		except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
			host = "localhost"
		
		try:
			port = config.getint(os.environ['RAMONA_SECTION'], 'port')
		except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
			port = 5588
		
		self.username = None
		self.password = None 
		try:
			self.username = config.get(os.environ['RAMONA_SECTION'], 'username')
			self.password = config.get(os.environ['RAMONA_SECTION'], 'password')
		except:
			pass
		
		if self.username is not None and self.password is None:
			L.fatal("Configuration error: 'username' option is set, but 'password' option is not set. Please set 'password'")
			sys.exit(1) 

		Handler = RamonaHttpReqHandler
		self.httpd = BaseHTTPServer.HTTPServer((host, port), Handler)
		
		# Prepare server connection factory
		self.cnsconuri = cnscom.socket_uri(config.get('ramona:console','serveruri'))
		
		self.logmsgcnt = itertools.count()
		self.logmsgs = dict()
		signal.signal(signal.SIGINT, self.stop)

	def run(self):
		L.info("Started HTTP frontend at http://{0}:{1}".format(self.httpd.server_name, self.httpd.server_port))
		self.httpd.serve_forever()
	
	def stop(self, signum, frame):
		L.info("Received signal {0}. Stopping the server.".format(signum))
		self.httpd.shutdown()


class RamonaHttpReqHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	
	ActionToCallid = {"start": cnscom.callid_start, "stop": cnscom.callid_stop, "restart": cnscom.callid_restart}
	scriptdir = os.path.dirname(__file__)
	
	def do_GET(self):
		
		if self.path.startswith("/static/"):
			parts = self.path.split("/")
			fname = os.path.join(self.scriptdir, *[x for x in parts if len(x) > 0])
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
				return
		
		authheader = self.headers.getheader("Authorization", None)
		if httpfend_app.instance.username is not None and authheader is None:
			self.serve_auth_headers()
			return
		
		elif httpfend_app.instance.username is not None and authheader is not None:
			method, authdata = authheader.split(" ") 
			if method != "Basic":
				self.send_error(httplib.NOT_IMPLEMENTED, "The authentication method '{0}' is not supported. Only Basic authnetication method is supported.".format(method))
				return
			username, _, password = base64.b64decode(authdata).partition(":")
			if httpfend_app.instance.password.startswith("{SHA}"):
				password = "{SHA}" + hashlib.sha1(password).hexdigest()
			
			if username != httpfend_app.instance.username or password != httpfend_app.instance.password:
				self.serve_auth_headers()
				return
		
		if self.path.startswith("/ajax/"):
			parsed = urlparse.urlparse(self.path)
			action = parsed.path[6:]
			if action == "statusTable":
				self.send_response(httplib.OK)
				self.send_header("Content-Type", "text/html; charset=utf-8")
				self.end_headers()
				self.wfile.write(self.buildStatusTable(json.loads(self.getStatuses())))
		
		elif self.path.startswith("/log/"):
			parsed = urlparse.urlparse(self.path)
			logname = parsed.path[5:]
			parts = logname.split("/")
			if len(parts) < 2:
				self.send_error(httplib.NOT_FOUND, "Invalid URL.")
				return
			stream = parts[0]
			if stream not in ("stdout", "stderr"):
				self.send_error(httplib.NOT_FOUND, "'{0}' is not a valid type of stream. Only 'stdout' and 'stderr' are supported.".format(stream))
				return
			program = urllib.unquote_plus(parts[1].rpartition(".")[0])
			conn = self.socket_connect()
			params = {
					"program": program,
					"stream": stream, 
			}
			try:
				ret = cnscom.svrcall(conn, cnscom.callid_tail, json.dumps(params))
				self.send_response(httplib.OK)
				self.send_header("Content-Type", "text/plain; charset=utf-8")
				self.end_headers()
				self.wfile.write(ret)
			except Exception, e:
				self.send_error(httplib.INTERNAL_SERVER_ERROR, str(e))
				return

		else:
			parsed = urlparse.urlparse(self.path)
			if parsed.path != "/":
				self.send_error(httplib.NOT_FOUND)
				return
			
			qs = urlparse.parse_qs(parsed.query)
			action = None
			actionList = qs.get('action')
			if actionList is not None and len(actionList) > 0:
				action = actionList[0]
			if action in ("start", "stop", "restart"):
				conn = self.socket_connect()
				params = {
					'immediate': True,
				}
				qsIdent = qs.get('ident')
				if qsIdent is not None and len(qsIdent) > 0:
					params['pfilter'] = [qsIdent[0]]
				else:
					params['pfilter'] = list(self.getAllPrograms(True))
				
				qsForce = qs.get('force')
				if qsForce is not None and len(qsForce) > 0:
					if qsForce[0] == "1":
						params['force'] = True
				
				try:
					cnscom.svrcall(conn, self.ActionToCallid[action], json.dumps(params))
					msgid = self.addLogMessage("success", "Command '{0}' successfully triggered.".format(action))
				except Exception, e:
					msgid = self.addLogMessage("error", "Failed to trigger the command: {0}".format(e))
				
				self.send_response(httplib.SEE_OTHER)
				self.send_header("Location", self.getAbsPath(msgid=msgid))
				self.end_headers()
				return
			
			self.send_response(httplib.OK)
			self.send_header("Content-Type", "text/html; charset=utf-8")
			self.end_headers()
			
			logmsg = ""
			for msgid in qs.get('msgid', []):
				m = httpfend_app.instance.logmsgs.pop(int(msgid), None)
				if m is not None:
					logmsg += '''<div class="alert alert-{0}">{1}</div>'''.format(*m)

			with open(os.path.join(self.scriptdir, "index.tmpl.html")) as f:
				sttable = self.buildStatusTable(json.loads(self.getStatuses()))
				self.wfile.write(f.read().format(
					statuses=sttable,
					logmsg=logmsg,
					appname=config.get('general','appname')
				))
				
	def log_message(self, fmt, *args):
		L.debug("{0} -- [{1}]: {2}".format(self.address_string(), self.log_date_time_string(), fmt % args))
			
	
	def buildStatusTable(self, statuses):
		ret = '<table id="statusTable" class="table table-hover table-bordered"><thead>'
		ret += '<tr><th>Process ident.</th><th>Status</th><th><abbr title="O = stdout, E = stderr">Log</abbr></th><th>PID</th><th><abbr title="Launch counter">L.cnt.</abbr></th><th>Start time</th><th>Exit time</th><th>Exit code</th><th></th></tr>'
		ret += "</thead>"
		ret += "<tbody>"
		for sp in statuses:
			ret += "<tr>"
			ident = sp.pop('ident', '???')
			ret += '<th>{0}</th>'.format(cgi.escape(ident))
			labelCls = "label-inverse"
			progState = sp.pop("state")
			
			if progState == cnscom.program_state_enum.RUNNING:
				labelCls = "label-success"
			elif progState == cnscom.program_state_enum.STOPPED:
				labelCls = ""
			elif progState in (cnscom.program_state_enum.STOPPING, cnscom.program_state_enum.STARTING):
				labelCls = "label-info"
			elif progState == cnscom.program_state_enum.STOPPED:
				labelCls = ""
			elif progState in (cnscom.program_state_enum.FATAL, cnscom.program_state_enum.CFGERROR):
				labelCls = "label-important"
			
			stlbl = cnscom.program_state_enum.labels.get(progState, "({0})".format(progState))
			ret += '<td><span class="label {0}">{1}</span></td>'.format(labelCls, cgi.escape(stlbl))
			ret += '<td><a href="/log/stdout/{0}.log" target="_blank">O</a> <a href="/log/stderr/{0}.log" target="_blank">E</a>'.format(urllib.quote_plus(ident))
			pid = sp.pop('pid', "")
			ret += '<td>{0}</td>'.format(pid)
			ret += '<td>{0}</td>'.format(sp.pop('launch_cnt', ""))

			u = sp.pop('uptime', None)
			if u is not None:
				t = sp.pop('start_time', '?')
				ret += '<td title="Started at {1}">{0}</td>'.format(natural_relative_time(u), time.strftime(STRFTIME_FMT,time.localtime(t)))
			else:
				t = sp.pop('start_time', None)
				tform = ""
				if t is not None: tform = time.strftime(STRFTIME_FMT,time.localtime(t))
				ret += '<td>{0}</td>'.format(tform)

			t = sp.pop('exit_time', None)
			tform = ""
			if t is not None: tform = time.strftime(STRFTIME_FMT,time.localtime(t))
			ret += '<td>{0}</td>'.format(tform)
			ret += '<td>{0}</td>'.format(sp.pop('exit_status',''))
			
			actions = []
			if pid != os.getpid():
				# TODO: Should there be some filtering for STOPPING ???
				if progState not in (cnscom.program_state_enum.FATAL, cnscom.program_state_enum.RUNNING, cnscom.program_state_enum.STARTING, cnscom.program_state_enum.DISABLED):
					actions.append('<a class="btn btn-small btn-success" href="/?{0}">Start</a>'.format(urllib.urlencode([("action", "start"), ("ident", ident)])))
				
				if progState == cnscom.program_state_enum.RUNNING:
					actions.append('<a class="btn btn-small btn-danger" href="/?{0}">Stop</a>'.format(urllib.urlencode([("action", "stop"), ("ident", ident)])))
					actions.append('<a class="btn btn-small btn-warning" href="/?{0}">Restart</a>'.format(urllib.urlencode([("action", "restart"), ("ident", ident)])))
			
				if progState == cnscom.program_state_enum.FATAL:
					actions.append('<a class="btn btn-small btn-inverse" href="/?{0}">Start (force)</a>'.format(urllib.urlencode([("action", "start"), ("ident", ident), ("force", "1")])))

			ret += '<td>{0}</td>'.format(" ".join(actions))
			ret += "</tr>"
			
			if len(sp) > 0:
				ret += '<tr class="info"><td colspan="2"></td><td colspan="7"><pre class="pre-scrollable">'
				ret += cgi.escape(pprint.pformat(sp, width=3))
				ret += '</pre></td></tr>'
		
		ret += "</tbody></table>"
		return ret
	
	
	def addLogMessage(self, level, msg):
		msgid = httpfend_app.instance.logmsgcnt.next()
		httpfend_app.instance.logmsgs[msgid] = (level, msg)
		return msgid
	
	def getAbsPath(self, path="/", **kwargs):
		queryList = []
		for k,v in kwargs.iteritems():
			queryList.append((k, v))
		
		return urlparse.urlunparse(("http", self.headers['Host'], "/", None, urllib.urlencode(queryList), None))
	
	def getStatuses(self):
		conn = self.socket_connect()
		return cnscom.svrcall(conn, cnscom.callid_status, json.dumps({}))
	
	def getAllPrograms(self, withoutSelf=False):
		'''
		@param withoutSelf: If true, the process with the same pid will be ignored
		@return iterator: Ident of all registered programs
		'''
		for st in json.loads(self.getStatuses()):
			ident = st.get("ident")
			pid = st.get("pid")
			if ident is None:
				continue
			if (not withoutSelf) or (pid != os.getpid()):
				yield ident
		
	
	def socket_connect(self):
		if hasattr(self, "socket_conn"): return self.socket_conn
		try:
			self.socket_conn = httpfend_app.instance.cnsconuri.create_socket_connect()
			return self.socket_conn
		except socket.error, e:
			if e.errno == errno.ECONNREFUSED: return None
			if e.errno == errno.ENOENT and self.cnsconuri.protocol == 'unix': return None
			raise
	
	def serve_auth_headers(self):
		self.send_response(httplib.UNAUTHORIZED)
		self.send_header('WWW-Authenticate', 'Basic realm="Ramona HTTP frontend"')
		self.send_header('Content-type', 'text/html')
		self.end_headers()
		with open(os.path.join(self.scriptdir, "401.tmpl.html")) as f:
			self.wfile.write(f.read().format(
					appname=config.get('general','appname'),
					configsection=os.environ['RAMONA_SECTION'])
			)
		

def natural_relative_time(diff_sec):
	#TODO: Improve this significantly - maybe even add unit test
	#if diff.days > 7 or diff.days < 0: return d.strftime('%d %b %y')
#	elif diff.days == 1:
#	    return '1 day ago'
#	elif diff.days > 1:
#	    return '{} days ago'.format(diff.days)
	if diff_sec <= 1:
		return 'just now'
	elif diff_sec < 60:
		return '{:0.1f} sec(s) ago'.format(diff_sec)
	elif diff_sec < 120:
		return '1 min ago'
	elif diff_sec < 3600:
		return '{:0.0f} min(s) ago'.format(diff_sec/60)
	elif diff_sec < 7200:
		return '1 hour ago'
	else:
		return '{:0.0f} hours ago'.format(diff_sec/3600)
