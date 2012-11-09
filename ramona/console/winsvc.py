#See http://code.activestate.com/recipes/551780/ for details 

# To debug use:
# > c:\Python27\Lib\site-packages\win32\pythonservice.exe -debug ramona-test ramonahttpfend

import os, sys, time
from os.path import splitext, abspath, join, dirname
from sys import modules

import win32serviceutil
import win32service
import win32api

from ..config import config, config_files

###

class w32_ramona_service(win32serviceutil.ServiceFramework):


	_svc_name_ = None
	_svc_display_name_ = 'Ramona Demo Service'

	@classmethod
	def configure(cls):
		assert cls._svc_name_ is None
		cls._svc_name_ = config.get('general','appname')
		# TODO: Allow user to provide display name via config
		cls._svc_display_name_ = config.get('general','appname')


	def __init__(self, *args):
		assert self._svc_name_ is None
		servicename = args[0][0]

		self.log("Ramona service '{0}' is starting".format(servicename))

		# Read working directory from registry and change to it
		directory = win32serviceutil.GetServiceCustomOption(servicename, 'directory')
		os.chdir(directory)

		# Set Ramona config environment variable to ensure proper configuration files load
		os.environ['RAMONA_CONFIG'] =  win32serviceutil.GetServiceCustomOption(servicename, 'config')

		from ..server.svrapp import server_app
		self.svrapp = server_app()
		self.configure()

		win32serviceutil.ServiceFramework.__init__(self, *args)


	def log(self, msg):
		import servicemanager
		servicemanager.LogInfoMsg(str(msg))


	def SvcDoRun(self):
		self.ReportServiceStatus(win32service.SERVICE_START_PENDING)

		try:
			self.ReportServiceStatus(win32service.SERVICE_RUNNING)
			self.log('Ramona service {0} is running'.format(self._svc_name_))
			self.svrapp.run()
			self.log('Quak')

		except SystemExit, e:
			self.log('SystemExit: {0}'.format(e))

		except Exception, e:
			self.log('Exception: {0}'.format(e))

		self.svrapp = None
		#self.ReportServiceStatus(win32service.SERVICE_STOPPED)


	def SvcStop(self):
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

		if self.svrapp is not None:
			self.svrapp.exitwatcher.send()
			while self.svrapp is not None:
				time.sleep(1)

		self.log('Ramona service {0} is stopped'.format(self._svc_name_))
		#self.ReportServiceStatus(win32service.SERVICE_STOPPED)

###

def w32_install_svc(start=False, server_only=True, programs=None):
	'''Install Windows Ramona Service'''

	import logging
	L = logging.getLogger('winsvc')

	directory = abspath(dirname(sys.argv[0])) # Find where console python prog is launched from ...

	cls = w32_ramona_service
	if cls._svc_name_ is None: cls.configure()

	try:
		module_path=modules[cls.__module__].__file__
	except AttributeError:
		# maybe py2exe went by
		from sys import executable
		module_path=executable
	module_file = splitext(abspath(join(module_path,'..','..', '..')))[0]
	cls._svc_reg_class_ = '{0}\\ramona.console.winsvc.{1}'.format(module_file, cls.__name__)

	win32api.SetConsoleCtrlHandler(lambda x: True, True) #  Service will stop on logout if False

	# Prepare command line
	cmdline = []
	if server_only: cmdline.append('-S')
	elif programs is not None: cmdline.extend(programs)

	# Install service
	win32serviceutil.InstallService(
		cls._svc_reg_class_,
		cls._svc_name_,
		cls._svc_display_name_,
		startType = win32service.SERVICE_AUTO_START,
		exeArgs = ' '.join(cmdline),
	)

	# Set directory from which Ramona server should be launched ...
	win32serviceutil.SetServiceCustomOption(cls._svc_name_, 'directory', directory)
	win32serviceutil.SetServiceCustomOption(cls._svc_name_, 'config', ';'.join(config_files))

	L.debug("Service {0} installed".format(cls._svc_name_))

	if start:
		x = win32serviceutil.StartService(cls._svc_name_)
		L.debug("Service {0} is starting ...".format(cls._svc_name_))
		#TODO: Wait for service start to check start status ...
		L.debug("Service {0} started".format(cls._svc_name_))

	return cls


def w32_uninstall_svc():
	'''Uninstall (remove) Windows Ramona Service'''

	import logging
	L = logging.getLogger('winsvc')

	cls = w32_ramona_service
	if cls._svc_name_ is None: cls.configure()

	scvType, svcState, svcControls, err, svcErr, svcCP, svcWH = win32serviceutil.QueryServiceStatus(cls._svc_name_)

	if svcState == win32service.SERVICE_RUNNING:
		L.debug("Service {0} is stopping ...".format(cls._svc_name_))
		win32serviceutil.StopService(cls._svc_name_)
		L.debug("Service {0} is stopped.".format(cls._svc_name_))

	win32serviceutil.RemoveService(cls._svc_name_)

	return cls
