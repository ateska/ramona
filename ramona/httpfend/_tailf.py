import logging
import pyev
from .. import cnscom

###

L = logging.getLogger("httpfendapp")

###

class tail_f_handler(object):
	
	def __init__(self, req_handler, cnsconn):
		self.loop = pyev.Loop()
		self.watchers = []
		self.req_handler = req_handler
		self.cnsconn = cnsconn
		self.watchers.append(self.loop.io(req_handler.rfile._sock, pyev.EV_READ, self.__on_rfile_io))
		self.watchers.append(self.loop.io(cnsconn._sock, pyev.EV_READ, self.__on_cns_io))
		
	def run(self):
		for watcher in self.watchers:
			watcher.start()
		self.loop.start()
			
	def __on_cns_io(self, watcher, events):
		retype, params = cnscom.svrresp(self.cnsconn, hang_detector=False)
		if retype == cnscom.resp_tailf_data:
			self.req_handler.wfile.write(params)
		else:
			raise RuntimeError("Unknown/invalid server response: {0}".format(retype))
	
	def __on_rfile_io(self, watcher, events):
		buf = self.req_handler.rfile.read(1)
		if len(buf) == 0:
			L.debug("Closing the tailf loop for client {0}".format(self.req_handler.client_address))
			self.loop.stop()
			return
		else:
			L.warning("Unexpected data received from the client: {}".format(buf))
