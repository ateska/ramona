import argparse

###

class _parser_base(argparse.ArgumentParser):

	argparser_kwargs = {}
	subparser_kwargs = {}

	def __init__(self):
		argparse.ArgumentParser.__init__(self, **self.argparser_kwargs)

		subparsers = self.add_subparsers(
			dest='subcommand',
			title='subcommands',
			parser_class=argparse.ArgumentParser,
		)
		
		# Adding sub-commands ...
		self.subcommands = {}
		for cmd in self.build_cmdlist():
			subparser = subparsers.add_parser(cmd.name, help=cmd.cmdhelp, **self.subparser_kwargs)
			cmd.init_parser(subparser)
			self.subcommands[cmd.name] = cmd


	def build_cmdlist(self):
		from .cnscmd import start
		yield start

		from .cnscmd import stop
		yield stop

		from .cnscmd import restart
		yield restart

		from .cnscmd import status
		yield status

		from .cnscmd import help
		yield help


	def parse(self, argv):
		self.args = self.parse_args(argv)
		

	def execute(self, cnsapp):
		if self.args.subcommand == 'help':
			# Help is given by special treatment as this is actually function of parser itself
			self.print_help()
			return

		return self.subcommands[self.args.subcommand].main(cnsapp, self.args)

#

class argparser(_parser_base):

	def __init__(self):
		_parser_base.__init__(self)

		# Add config file option
		self.add_argument('-c', '--config', metavar="CONFIGFILE", action='append', help='Specify config file(s) to read (this option can be given more times).')


	def build_cmdlist(self):
		for cmd in _parser_base.build_cmdlist(self): yield cmd

		from .cnscmd import console
		yield console

		from .cnscmd import server
		yield server

#

class consoleparser(_parser_base):

	argparser_kwargs = {'add_help': False, 'usage': argparse.SUPPRESS}
	subparser_kwargs = {'usage': argparse.SUPPRESS}

	def build_cmdlist(self):
		for cmd in _parser_base.build_cmdlist(self): yield cmd

		from .cnscmd import exit
		yield exit


	def error(self, message):
		print "Error:", message
		raise SyntaxError()

