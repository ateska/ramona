#!/usr/bin/env python
import os
import ramona

class TestConsoleApp(ramona.console_app):
	'''This application serves mostly for testing
	The programs run by this application usually fails to test different corner cases.
	'''  
	pass

if __name__ == '__main__':
	app = TestConsoleApp(configuration='./test.conf')
	app.run()
