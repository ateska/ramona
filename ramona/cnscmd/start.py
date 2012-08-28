import time
from .. import cnscom
#
name = 'start'
cmdhelp = 'Launch subprocess(es)'

###

def init_parser(parser):
	return

###

def main(cnsapp, args):

	# Fist check if ramona server is running and if not, launch that
	s = cnsapp.connect()
	if s is None:
		#TODO: This is only verbose print
		print "It looks like server is not running - launching server"
		launch_server()
		
		for _ in range(100): # Check server availability for next 10 seconds 
			time.sleep(0.1)
			s = cnsapp.connect()
			if s is not None: break

	if s is None:
		print "Server process launch failed"
		cnsapp.exitcode = 5
		return

	cnsapp.svrcall(cnscom.callid_start)

#

def launch_server():
	from ..utils import daemonize
	ret = daemonize()
	if ret != 0:
		print "Child is running"
		return

	from ..utils import launch_server
	launch_server()
