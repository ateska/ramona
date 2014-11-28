#!/usr/bin/env python2
#
# Released under the BSD license. See LICENSE.txt file for details.
#
import ramona

class TestConsoleApp(ramona.console_app):
	"""
	This application serves mostly for testing and as example.
	The programs run by this application usually fails to test
	different corner cases.
	"""
	
	pass
	
if __name__ == '__main__':
	app = TestConsoleApp(configuration='./test.conf')
	app.run()
