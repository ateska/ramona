import logging
import pywintypes # from Python Win32
from ..winsvc import w32_install_svc

###

name = 'wininstall'
cmdhelp = 'Install Ramona as Windows Service (Windows only)'

###


L = logging.getLogger('wininstall')

###

def init_parser(parser):
	parser.add_argument('-s', '--start', action='store_true', help='Start installed service after installation.')
	# Auto-start of server
	# Auto-start of programs (maybe specify which - the same way as in start command)

###

def main(cnsapp, args):
	try:
		cls = w32_install_svc(start=args.start)
	except pywintypes.error, e:
		L.error("Error when installing Windows service: {0} ({1})".format(e.strerror, e.winerror))
		return 3 # Exit code

	if args.start:
		L.info("Windows service '{0}' has been installed and started successfully.".format(cls._svc_name_))
	else:
		L.info("Windows service '{0}' has been installed successfully.".format(cls._svc_name_))
