import logging
import pywintypes # from Python Win32
from ..winsvc import w32_uninstall_svc

###

name = 'winuninstall'
cmdhelp = 'Uninstall the Ramona Windows Service (Windows only)'

###


L = logging.getLogger('winuninstall')

###

def init_parser(parser):
	pass

###

def main(cnsapp, args):
	try:
		cls = w32_uninstall_svc()
	except pywintypes.error, e:
		L.error("Error when uninstalling Windows service: {0} ({1})".format(e.strerror, e.winerror))
		return 3 # Exit code

	L.info("Windows service '{0}' has been uninstalled.".format(cls._svc_name_))
