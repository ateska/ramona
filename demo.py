#!/usr/bin/env python
#
# Released under the BSD license. See LICENSE.txt file for details.
#
import os
import ramona

class MyDemoConsoleApp(ramona.console_app):

    @ramona.tool
    def tool_demo(self):
        """Printing message about demo of custom ramona.tool"""
        print "This is an implementation of a custom tool (see ./demo.sh --help)"
        # Example of how to access configuration from tools
        print "Value of env:RAMONADEMO = {0}".format(self.config.get("env", "RAMONADEMO"))

    @ramona.tool
    class tool_class_demo(object):
        """Demo of custom ramona.tool (class)"""

        def init_parser(self, cnsapp, parser):
            parser.description = 'You can use methods from argparse module of Python to customize tool (sub)parser.'
            parser.add_argument('integers', metavar='N', type=int, nargs='+', 
                help='an integer for the accumulator'
            )
            parser.add_argument('--sum', const=sum, default=max,
                dest='accumulate', action='store_const',
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
