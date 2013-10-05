import weakref

#

class server_app_singleton(object):
	'''
	Providing server application singleton construct and 
	more importantly also server_app_singleton.instance weak reference (that points to top level application object)
	'''

	instance = None

	def __init__(self):
		assert server_app_singleton.instance is None
		server_app_singleton.instance = weakref.ref(self)

	def __del__(self):
		server_app_singleton.instance = None


def get_svrapp():
	if server_app_singleton.instance is None: return None
	return server_app_singleton.instance()
