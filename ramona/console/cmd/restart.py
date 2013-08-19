import json
from ... import cnscom
from ._completions import complete_ident

###

name = 'restart'
cmdhelp = 'Restart program(s)'

###

def init_parser(parser):
	parser.add_argument('-n','--no-server-start', action='store_true', help='Avoid eventual automatic Ramona server start')
	parser.add_argument('-i','--immediate-return', action='store_true', help="Don't wait for restart of programs and exit ASAP")
	parser.add_argument('-f','--force-start', action='store_true', help='Force restart of programs even in FATAL state')
	parser.add_argument('program', nargs='*', help='Optionally specify program(s) in scope of the command. If none is given, all programs are considered in scope.')

###

def complete(console, text, line, begidx, endidx):
	textst = text.strip()
	ret = []
	ret.extend(complete_ident(console, textst))
	return ret

###

def main(cnsapp, args):
	params={
		'force':args.force_start,
		'immediate': args.immediate_return,
	}
	if len(args.program) > 0: params['pfilter'] = args.program

	cnsapp.cnssvrcall(
		cnscom.callid_restart,
		json.dumps(params),
		auto_connect=args.no_server_start,
		auto_server_start=not args.no_server_start
	)
