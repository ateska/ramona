import logging, functools
import pyev
###

L = logging.getLogger("idlework")

###

def _execute(w):
	# Launch worker safely
	try:
		w()
	# except SystemExit, e:
	# 	L.debug("Idle worker requested system exit")
	# 	self.Terminate(e.code)
	except:
		L.exception("Exception during idle worker")


###

class idlework_appmixin(object):


	def __init__(self):
		self.idle_queue = []
		self.idle_watcher = pyev.Idle(self.loop, self.__idle_cb)


	def stop_idlework(self):
		self.idle_watcher.stop()
		self.idle_watcher = None

		while len(self.idle_queue) > 0:
			w = self.idle_queue.pop(0)
			_execute(w)


	def __del__(self):
		try:
			self.idle_watcher.stop()
		except AttributeError:
			pass


	def __idle_cb(self, watcher, revents):
		w = self.idle_queue.pop(0)

		if len(self.idle_queue) == 0:
			self.idle_watcher.stop()

		_execute(w)


	def add_idlework(self, worker, *args, **kwargs):
		'''
		Add worker (callable) to idle work queue.
		@param worker: Callable that will be invoked when applicaiton loops idles
		@param *args: Optional positional arguments that will be supplied to worker callable
		@param **kwargs: Optional keywork arguments that will be supplied to worker callable
		'''
		if len(args) > 0 or len(kwargs) > 0:
			worker = functools.partial(worker, *args, **kwargs)
		
		self.idle_queue.append(worker)
		self.idle_watcher.start()
