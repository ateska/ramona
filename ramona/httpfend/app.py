import sys, os, socket, ConfigParser, errno, logging, httplib, BaseHTTPServer, mimetypes, json, signal, threading
import time, cgi, pprint, urllib, urlparse, itertools, base64, hashlib, pkgutil, zipimport, collections
import pyev
from ..config import config, read_config, get_numeric_loglevel
from .. import cnscom, socketuri

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

	STOPSIGNALS = [signal.SIGINT, signal.SIGTERM]
	NONBLOCKING = frozenset([errno.EAGAIN, errno.EWOULDBLOCK])
	
	def __init__(self):
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
			self.listenaddr = config.get(os.environ['RAMONA_SECTION'], 'listen')
		except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
			self.listenaddr = "tcp://localhost:5588"
		
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
		
		# Prepare server connection factory
		self.cnsconuri = socketuri.socket_uri(config.get('ramona:console','serveruri'))
		
		self.logmsgcnt = itertools.count()
		self.logmsgs = dict()
			
		self.workers = collections.deque() 

		self.svrsockets = []
		
		for addr in self.listenaddr.split(','):
			socket_factory = socketuri.socket_uri(addr)
			try:
				socks = socket_factory.create_socket_listen()
			except socket.error, e:
				L.fatal("It looks like that server is already running: {0}".format(e))
				sys.exit(1)
			self.svrsockets.extend(socks)

		if len(self.svrsockets) == 0:
			L.fatal("There is no http server listen address configured - considering this as fatal error")
			sys.exit(1)

		self.loop = pyev.default_loop()
		self.watchers = [pyev.Signal(sig, self.loop, self.__terminal_signal_cb) for sig in self.STOPSIGNALS]
		
		for sock in self.svrsockets:
			sock.setblocking(0)
			self.watchers.append(pyev.Io(sock._sock, pyev.EV_READ, self.loop, self.__on_accept))
		
	def run(self):
		
		for sock in self.svrsockets:
			sock.listen(socket.SOMAXCONN)
			L.debug("Ramona HTTP frontend is listening at {0}".format(sock.getsockname()))
		for watcher in self.watchers:
			watcher.start()

		L.info('Ramona HTTP frontend started and is available at {0}'.format(self.listenaddr))

		# Launch loop
		try:
			self.loop.start()
		finally:
			for w in self.workers:
				w.join(0.5)

	def __on_accept(self, watcher, events):
		# Fist find relevant socket
		sock = None
		for s in self.svrsockets:
			if s.fileno() == watcher.fd:
				sock = s
				break
		if sock is None:
			L.warning("Received accept request on unknown socket {0}".format(watcher.fd))
			return
		# Accept all connection that are pending in listen backlog
		while True:
			try:
				clisock, address = sock.accept()
				
			except socket.error as err:
				if err.args[0] in self.NONBLOCKING:
					break
				else:
					raise
			else:
				worker = RequestWorker(clisock, address, self)
				worker.start()
				self.workers.append(worker)
	
	def __terminal_signal_cb(self, watcher, events):
		watcher.loop.stop()

#

class RequestWorker(threading.Thread):
	
	def __init__(self, sock, address, server):
		threading.Thread.__init__(self, name="worker")
		self.sock = sock
		self.address = address
		self.server = server
	
	def run(self):
		try:
			RamonaHttpReqHandler(self.sock, self.address, self.server)
		except:
			L.exception("Uncaught exception during worker thread execution:")
		finally:
			self.server.workers.remove(self)

#

def _is_egg():
	ret = isinstance(pkgutil.get_loader(__name__), zipimport.zipimporter)
	return ret

_scriptdir = os.path.dirname(__file__)
def _static_file_exists(path):
	if _is_egg():
		from pkg_resources import resource_exists
		if path.startswith("/"): path = path[1:]
		return resource_exists("ramona.httpfend", path)
	else:
		parts = path.split("/")
		fname = os.path.join(_scriptdir, *[x for x in parts if len(x) > 0])
		return os.path.isfile(fname)
	return True

def _get_static_file(path):
	if _is_egg():
		from pkg_resources import resource_stream
		if path.startswith("/"): path = path[1:]
		return resource_stream("ramona.httpfend", path)

	else:
		parts = path.split("/")
		return open(os.path.join(_scriptdir, *[x for x in parts if len(x) > 0]), "rb")

#

class RamonaHttpReqHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	
	def __init__(self, request, client_address, server):
		BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, request, client_address, server)
		self.server = server
	
	ActionToCallid = {"start": cnscom.callid_start, "stop": cnscom.callid_stop, "restart": cnscom.callid_restart}
	_scriptdir = os.path.dirname(__file__)
	
	def do_GET(self):
		
		if self.path.startswith("/static/"):
			parts = self.path.split("/")
			if not _static_file_exists(self.path):
				self.send_error(httplib.NOT_FOUND)
				return
			try:
				f = _get_static_file(self.path)
			except IOError:
				self.send_error(httplib.NOT_FOUND)
				return
			try:
				self.send_response(httplib.OK)
				self.send_header("Content-Type", mimetypes.guess_type(self.path)[0])
				self.end_headers()
				self.wfile.write(f.read())
				return
			finally:
				f.close()
		
		authheader = self.headers.getheader("Authorization", None)
		if self.server.username is not None and authheader is None:
			self.serve_auth_headers()
			return
		
		elif self.server.username is not None and authheader is not None:
			method, authdata = authheader.split(" ") 
			if method != "Basic":
				self.send_error(httplib.NOT_IMPLEMENTED, "The authentication method '{0}' is not supported. Only Basic authnetication method is supported.".format(method))
				return
			username, _, password = base64.b64decode(authdata).partition(":")
			if self.server.password.startswith("{SHA}"):
				password = "{SHA}" + hashlib.sha1(password).hexdigest()
			
			if username != self.server.username or password != self.server.password:
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
				m = self.server.logmsgs.pop(int(msgid), None)
				if m is not None:
					logmsg += '''<div class="alert alert-{0}">{1}</div>'''.format(*m)

			f = _get_static_file("index.tmpl.html")
			try:
				sttable = self.buildStatusTable(json.loads(self.getStatuses()))
				self.wfile.write(f.read().format(
					statuses=sttable,
					logmsg=logmsg,
					appname=config.get('general','appname')
				))
			finally:
				f.close()
	
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
		msgid = self.server.logmsgcnt.next()
		self.server.logmsgs[msgid] = (level, msg)
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
			self.socket_conn = self.server.cnsconuri.create_socket_connect()
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
		f = _get_static_file("401.tmpl.html")
		try:
			self.wfile.write(f.read().format(
					appname=config.get('general','appname'),
					configsection=os.environ['RAMONA_SECTION'])
			)
		finally:
			f.close()
		

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
