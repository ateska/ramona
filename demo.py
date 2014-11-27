#!/usr/bin/env python2
#
# Released under the BSD license. See LICENSE.txt file for details.
#
import os
import ramona

class MyDemoConsoleApp(ramona.console_app):

	@ramona.tool
	def tool_demo(self):
		"""Printing message about demo of custom ramona.tool"""
		print "This is implementation of custom tool (see ./demo.sh --help)"
		# Example how to access configuration from tool:
		print "Value of env:RAMONADEMO = {0}".format(self.config.get("env", "RAMONADEMO"))
		env = ramona.config.get_env()
		print "All environment variables", env
		print
		env_alternative1 = ramona.config.get_env("alternative1")
		print "All alternative1 environment variables", env_alternative1



	@ramona.tool
	class tool_class_demo(object):
		"""Demo of custom ramona.tool (class)"""

		def init_parser(self, cnsapp, parser):
			parser.description = 'You can use methods from argparse module of Python to customize tool (sub)parser.'
			parser.add_argument('integers', metavar='N', type=int, nargs='+', 
				help='an integer for the accumulator'
			)
			parser.add_argument('--sum', dest='accumulate', action='store_const',
				const=sum, default=max,
				help='sum the integers (default: find the max)'
			)

		def main(self, cnsapp, args):
			print args.accumulate(args.integers)


	@ramona.proxy_tool
	def proxy_tool_demo(self, argv):
		"""Proxying execution of /bin/ls"""
		os.execv('/bin/ls', argv)


if __name__ == '__main__':
	app = MyDemoConsoleApp(configuration='./demo.conf')
	app.run()
