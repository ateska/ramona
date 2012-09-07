import cmd, logging
import readline #TODO: optional
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

class _console_cmd(cmd.Cmd):


	def __init__(self, cnsapp):
		cmd.Cmd.__init__(self)
		self.prompt = '> '
		self.cnsapp = cnsapp


	def onecmd(self, line):
		if line == 'EOF':
			print ""
			return True

		line = line.strip()
		if line == '':
			# Send 'ping' to server
			try:
				self.cnsapp.svrcall(cnscom.callid_ping, '', auto_connect=True)
			except Exception, e:
				L.error("{0}".format(e))
			return False

		if line == '?':
			line = 'help'

		from ..parser import consoleparser
		
		parser = consoleparser(self.cnsapp)
		
		try:
			parser.parse(line.split())
		except SyntaxError:
			return False
		except SystemExit:
			return False

		try:
			parser.execute(self.cnsapp)
		except Exception, e:
			L.error("{0}".format(e))

		return False

#

def main(cnsapp, args):
	old_is_interactive = cnsapp.is_interactive
	cnsapp.is_interactive = True
	try:
		L.info("Ramona console for {0}".format(config.get('general','appname'))) #TODO: Add version info

		histfile = config.get('ramona:console', 'history')
		if histfile != '':
			try:
				readline.read_history_file(histfile)
			except IOError:
				pass

		c = _console_cmd(cnsapp)
		try:
			c.cmdloop()
		
		except KeyboardInterrupt:
			print ""
		
		finally:
			if histfile != '': readline.write_history_file(histfile)
	finally:
		cnsapp.is_interactive = old_is_interactive
