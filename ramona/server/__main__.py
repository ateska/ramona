'''
This code is stub/kickstarted for ramona server application 
'''

# This code can be used to enable remote debugging in PyDev
#Add pydevd to the PYTHONPATH (may be skipped if that path is already added in the PyDev configurations)
#import sys;sys.path.append(r'/opt/eclipse4.2/plugins/org.python.pydev_2.6.0.2012062818/pysrc')
#import pydevd
#pydevd.settrace()

###

if __name__ == "__main__":
	from .app import server_app
	svrapp = server_app()
	svrapp.run()
