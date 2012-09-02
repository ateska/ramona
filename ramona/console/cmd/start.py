import time
from ... import cnscom
from ...utils import launch_server, launch_server_daemonized
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
		print "It looks like Ramona server is not running - launching server"
		launch_server_daemonized()

		for _ in range(100): # Check server availability for next 10 seconds 
			time.sleep(0.1)
			s = cnsapp.connect()
			if s is not None: break

	if s is None:
		print "Ramona server process start failed"
		cnsapp.exitcode = 5
		return

	cnsapp.svrcall(cnscom.callid_start)

