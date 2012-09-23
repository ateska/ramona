import argparse

###

class _parser_base(argparse.ArgumentParser):

	argparser_kwargs = {}
	subparser_kwargs = {}

	def __init__(self, cnsapp):
		argparse.ArgumentParser.__init__(self, **self.argparser_kwargs)

		self.subparsers = self.add_subparsers(
			dest='subcommand',
			title='subcommands',
			parser_class=argparse.ArgumentParser,
		)
		
		# Adding sub-commands ...
		self.subcommands = {}
		for cmd in self.build_cmdlist():
			subparser = self.subparsers.add_parser(cmd.name, help=cmd.cmdhelp, **self.subparser_kwargs)
			cmd.init_parser(subparser)
			self.subcommands[cmd.name] = cmd

		#Iterate via application object to find 'tool' and 'proxy_tool' (decorated method)
		for mn in dir(cnsapp):
			fn = getattr(cnsapp, mn)
			if hasattr(fn, 'tool'):
				self.subparsers.add_parser(mn, help=fn.__doc__)
				self.subcommands[mn] = fn.im_func # Unbound method
			elif hasattr(fn, 'proxy_tool'):
				self.subparsers.add_parser(mn, help=fn.__doc__)
				# Not subcommand as proxy tools are handled prior argument parsing


	def build_cmdlist(self):
		from .cmd import start
		yield start

		from .cmd import stop
		yield stop

		from .cmd import restart
		yield restart

		from .cmd import status
		yield status

		from .cmd import help
		yield help

		from .cmd import tail
		yield tail


	def parse(self, argv):
		self.args = None # This is to allow re-entrant parsing
		self.args = self.parse_args(argv)
		

	def execute(self, cnsapp):
		if self.args.subcommand == 'help':
			# Help is given by special treatment as this is actually function of parser itself
			self.print_help()
			return

		cmdobj = self.subcommands[self.args.subcommand]

		if hasattr(cmdobj,'__call__'):
			return cmdobj(cnsapp)
		else:
			return cmdobj.main(cnsapp, self.args)

#

class argparser(_parser_base):

	def __init__(self, cnsapp):
		_parser_base.__init__(self, cnsapp)

		# Add config file option
		self.add_argument('-c', '--config', metavar="CONFIGFILE", action='append', help='Specify configuration file(s) to read (this option can be given more times). This will override build-in application level configuration.')

		# Add debug log level option
		self.add_argument('-d', '--debug', action='store_true', help='Enable debug (verbose) output.')

		# Add silent log level option
		self.add_argument('-s', '--silent', action='store_true', help='Enable silent mode of operation (only errors are printed).')


	def build_cmdlist(self):
		for cmd in _parser_base.build_cmdlist(self): yield cmd

		from .cmd import console
		yield console

		from .cmd import server
		yield server

#

class consoleparser(_parser_base):

	argparser_kwargs = {'add_help': False, 'usage': argparse.SUPPRESS}
	subparser_kwargs = {'usage': argparse.SUPPRESS}

	def build_cmdlist(self):
		for cmd in _parser_base.build_cmdlist(self): yield cmd

		from .cmd import exit
		yield exit


	def error(self, message):
		print "Error:", message
		raise SyntaxError()

