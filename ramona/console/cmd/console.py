import cmd, logging
import readline #TODO: optional
from ...config import config

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
		if line == '': return False

		if line == '?':
			line = 'help'

		from ..parser import consoleparser
		
		parser = consoleparser()
		
		try:
			parser.parse(line.split())
		except SyntaxError:
			return False
		except SystemExit:
			return False

		self.cnsapp.exitcode = None
		parser.execute(self.cnsapp)
		if (self.cnsapp.exitcode is not None) and (self.cnsapp.exitcode != 0):
			L.error("Last command failed.")

		return False

#

def main(cnsapp, args):
	
	histfile = config.get('ramona:console', 'history')
	if histfile != '':
		try:
			readline.read_history_file(histfile)
		except IOError:
			pass

	L.info("Ramona console") #TODO: Add version info

	c = _console_cmd(cnsapp)
	try:
		c.cmdloop()
	
	except KeyboardInterrupt:
		print ""
	
	finally:
		if histfile != '': readline.write_history_file(histfile)
