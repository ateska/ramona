import time, logging
from ... import cnscom
from ...utils import launch_server, launch_server_daemonized
#
name = 'start'
cmdhelp = 'Launch subprocess(es)'

###

L = logging.getLogger('start')

###

def init_parser(parser):
	return

###

def main(cnsapp, args):

	# Fist check if ramona server is running and if not, launch that
	s = cnsapp.connect()
	if s is None:
		L.debug("It looks like Ramona server is not running - launching server")
		launch_server_daemonized()

		for _ in range(100): # Check server availability for next 10 seconds 
			# TODO: Also improve 'crash-start' detection (to reduce lag when server fails to start)
			time.sleep(0.1)
			s = cnsapp.connect()
			if s is not None: break

	if s is None:
		raise server_start_error("Ramona server process start failed")

	cnsapp.svrcall(cnscom.callid_start)

