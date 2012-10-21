#See http://code.activestate.com/recipes/551780/ for details 

import os, sys
from os.path import splitext, abspath, join, dirname
from sys import modules

import win32serviceutil
import win32service
import win32event
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

		# Read working directory from registry and change to it
		directory = win32serviceutil.GetServiceCustomOption(args[0], 'directory')
		os.chdir(directory)

		# Set Ramona config environment variable to ensure proper configuration files load
		os.environ['RAMONA_CONFIG'] =  win32serviceutil.GetServiceCustomOption(args[0], 'config')

		from ..server.svrapp import server_app
		self.svrapp = server_app()
		self.configure()
		self.log(">>> {0}".format(config_files))

		win32serviceutil.ServiceFramework.__init__(self, *args)
		self.stop_event = win32event.CreateEvent(None, 0, 0, None)


	def log(self, msg):
		import servicemanager
		servicemanager.LogInfoMsg(str(msg))


	def SvcDoRun(self):
		self.ReportServiceStatus(win32service.SERVICE_START_PENDING)

		try:
			self.ReportServiceStatus(win32service.SERVICE_RUNNING)
			self.log('Ramona service {0} is running'.format(self._svc_name_))
			self.svrapp.run()
			win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)

		except SystemExit, e:
			self.svrapp = None
			self.SvcStop()

		except Exception, e:
			self.svrapp = None
			self.log('Exception : {0}'.format(e))
			self.SvcStop()


	def SvcStop(self):
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
		self.stop()
		self.log('Ramona service {0} is stopped'.format(self._svc_name_))
		win32event.SetEvent(self.stop_event)
		self.ReportServiceStatus(win32service.SERVICE_STOPPED)


	def stop(self):
		if self.svrapp is not None:
			self.svrapp.exitwatcher.send()

###

def w32_install_svc():
	''' Install Win32 Ramona Service'''

	directory = abspath(dirname(sys.argv[0])) # Find where console python prog is launched from ...

	cls = w32_ramona_service
	cls.configure()

	try:
		module_path=modules[cls.__module__].__file__
	except AttributeError:
		# maybe py2exe went by
		from sys import executable
		module_path=executable
	module_file = splitext(abspath(join(module_path,'..','..', '..')))[0]
	cls._svc_reg_class_ = '{0}\\ramona.console.w32svc.{1}'.format(module_file, cls.__name__)

	win32api.SetConsoleCtrlHandler(lambda x: True, True) #  Service will stop on logout if False

	#TODO: Add eventual list of config files as 'exeArgs' to pass this info to server
	win32serviceutil.InstallService(
		cls._svc_reg_class_,
		cls._svc_name_,
		cls._svc_display_name_,
		startType = win32service.SERVICE_AUTO_START,
	)

	# Set directory from which Ramona server should be launched ...
	win32serviceutil.SetServiceCustomOption(cls._svc_name_, 'directory', directory)
	win32serviceutil.SetServiceCustomOption(cls._svc_name_, 'config', ';'.join(config_files))

	return cls

		# print 'Install ok'
		# win32serviceutil.StartService(
		# 	cls._svc_name_
		# )
