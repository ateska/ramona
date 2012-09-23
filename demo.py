#!/usr/bin/env python
import os
import ramona

class MyDemoConsoleApp(ramona.console_app):

	@ramona.tool
	def tool_demo(self):
		'''Printing message about demo of custom ramona.tool'''
		print "This is implementation of custom tool (see ./demo --help)"


	@ramona.proxy_tool
	def proxy_tool_demo(self, argv):
		'''Proxying execution of /bin/ls'''
		os.execv('/bin/ls', argv)


if __name__ == '__main__':
	app = MyDemoConsoleApp(configuration='./demo.conf')
	app.run()
