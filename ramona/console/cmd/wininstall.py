import logging
import pywintypes # from Python Win32
from ..w32svc import w32_install_svc

###

name = 'wininstall'
cmdhelp = 'Install Ramona as Windows Service (Windows only)'

###


L = logging.getLogger('wininstall')

###

def init_parser(parser):
	return

###

def main(cnsapp, args):
	try:
		cls = w32_install_svc()
	except pywintypes.error, e:
		L.error("Error when installing Windows service: {0} ({1})".format(e.strerror, e.winerror))
		return 3 # Exit code

	L.info("Windows service '{0}' has been installed successfully.".format(cls._svc_name_))
