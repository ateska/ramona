#!/usr/bin/env python
import ramona

class MyDemoConsoleApp(ramona.console_app):
	pass

if __name__ == '__main__':
	app = MyDemoConsoleApp()
	app.run()
 

 #TODO: clean -> find . -name "*.pyc" -or -name "*.pyo" | xargs rm
 