#!/usr/bin/env python
import ramona

class MyDemoConsoleApp(ramona.console_app):
	#TODO: Tool example
	pass

if __name__ == '__main__':
	app = MyDemoConsoleApp(configuration='./demo.conf')
	app.run()
