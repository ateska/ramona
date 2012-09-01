'''
This code is stub/kickstarted for ramona server application 
'''

if __name__ == "__main__":
	import os
	os.system("lsof -p {0}".format(os.getpid()))

	from .app import server_app
	svrapp = server_app()
	svrapp.run()
