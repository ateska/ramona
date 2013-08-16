from .. import exception

###

name = 'server'
cmdhelp = 'Start the Ramona server in the foreground'

###

def init_parser(parser):
	parser.add_argument('-S','--server-only', action='store_true', help='Start only server, programs are not launched')
	parser.add_argument('program', nargs='*', help='Optionally specify program(s) in scope of the command. If none is given, all programs are considered in scope.')

###

def main(cnsapp, args):
	if args.server_only:
		if len(args.program) > 0:
			raise exception.parameters_error('Cannot specify programs and -S option at once.')

	from ...utils import launch_server
	launch_server(args.server_only, args.program)
