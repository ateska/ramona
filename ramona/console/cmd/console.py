import os, cmd, logging, sys, functools
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

try:
	import readline
except ImportError:
	readline = None

if readline is not None:
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
		for cmdname, cmditem in self.parser.subcommands.iteritems():
			def do_cmd_template(self, _cmdline):
				try:
					self.parser.execute(self.cnsapp)
				except Exception, e:
					L.error("{0}".format(e))

			setattr(self.__class__, "do_{0}".format(cmdname), do_cmd_template)
			
			if hasattr(cmditem, "complete"):
				setattr(self.__class__, "complete_{0}".format(cmdname), cmditem.complete)

		# Add also proxy_tools
		self.proxy_tool_set = set()
		for mn in dir(cnsapp):
			fn = getattr(cnsapp, mn)
			if not hasattr(fn, '__proxy_tool'): continue

			self.proxy_tool_set.add(mn)
			setattr(self.__class__, "do_{0}".format(mn), functools.partial(launch_proxy_tool, fn, mn))


		cmd.Cmd.__init__(self)


	def precmd(self, line):
		if line == '': return ''
		if line == "EOF":
			print
			sys.exit(0)

		# Check if this is proxy tool - if yes, then bypass parser
		try:
			farg, _ = line.split(' ',1)
		except ValueError:
			farg = line
		farg = farg.strip()
		if farg in self.proxy_tool_set:
			return line

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
			self.cnsapp.cnssvrcall(cnscom.callid_ping, '', auto_connect=True)
		except Exception, e:
			L.error("{0}".format(e))
	
#

def main(cnsapp, args):
	from ... import version as ramona_version
	L.info("Ramona (version {0}) console for {1}".format(ramona_version, config.get('general','appname')))

	histfile = config.get('ramona:console', 'history')
	if histfile != '':
		histfile = os.path.expanduser(histfile)
		try:
			if readline is not None: readline.read_history_file(histfile)
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
		if readline is not None and histfile != '':
			try:
				readline.write_history_file(histfile)
			except Exception, e:
				L.warning("Cannot write console history file '{1}': {0}".format(e, histfile))

#

def launch_proxy_tool(fn, cmd, cmdline):
	'''
	To launch proxy tool, we need to fork and then call proxy_tool method in child.
	Parent is waiting for child exit ...
	'''
	cmdline = cmdline.split(' ')
	cmdline.insert(0, cmd)

	pid = os.fork()
	if pid == 0:
		# Child
		try:
			fn(cmdline)
		except Exception, e:
			print "Execution of tool failed: ", e
		os._exit(0)
	else:
		# Parent
		ret = os.waitpid(pid, 0) # Wait for child process to finish

