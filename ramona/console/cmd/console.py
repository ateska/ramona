import os, cmd, logging, sys
from ...config import config
from ... import cnscom

###

name = 'console'
cmdhelp = 'Enter interactive console mode'

###

L = logging.getLogger("console")

###

def init_parser(parser):
	return

###

import readline #TODO: optional

# See http://stackoverflow.com/questions/7116038/python-tab-completion-mac-osx-10-7-lion
if 'libedit' in readline.__doc__:
	readline.parse_and_bind("bind ^I rl_complete")
else:
	readline.parse_and_bind("tab: complete")

###

class _console_cmd(cmd.Cmd):


	def __init__(self, cnsapp):
		self.prompt = '> '
		self.cnsapp = cnsapp

		from ..parser import consoleparser
		self.parser = consoleparser(self.cnsapp)

		# Build dummy method for each command in the parser
		for m in self.parser.subcommands.keys():
			def do_cmd_template(self, _cmdline):
				try:
					self.parser.execute(self.cnsapp)
				except Exception, e:
					L.error("{0}".format(e))

			setattr(self.__class__, "do_{0}".format(m), do_cmd_template)

		cmd.Cmd.__init__(self)
	

	def precmd(self, line):
		if line == '': return ''
		if line == "EOF":
			print
			sys.exit(0)
			
		try:
			self.parser.parse(line.split())
		except SyntaxError: # To capture cases like 'xxx' (avoid exiting)
			self.parser.parse(['help'])
			return 'help'
		except SystemExit: # To capture cases like 'tail -xxx' (avoid exiting)
			self.parser.parse(['help'])
			return 'help'
		return line


	def emptyline(self):
		# Send 'ping' to server
		try:
			self.cnsapp.svrcall(cnscom.callid_ping, '', auto_connect=True)
		except Exception, e:
			L.error("{0}".format(e))
	
#

def main(cnsapp, args):
	old_is_interactive = cnsapp.is_interactive
	cnsapp.is_interactive = True
	try:
		L.info("Ramona console for {0}".format(config.get('general','appname'))) #TODO: Add version info

		histfile = config.get('ramona:console', 'history')
		if histfile != '':
			histfile = os.path.expanduser(histfile)
			try:
				readline.read_history_file(histfile)
			except IOError:
				pass

		c = _console_cmd(cnsapp)
		try:
			c.cmdloop()
		
		except Exception, e:
			L.exception("Exception during cmd loop:")

		except KeyboardInterrupt:
			print ""
		
		finally:
			if histfile != '':
				try:
					readline.write_history_file(histfile)
				except Exception, e:
					L.warning("Cannot write console history file '{1}': {0}".format(e, histfile))
	finally:
		cnsapp.is_interactive = old_is_interactive
