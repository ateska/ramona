import json
from ... import cnscom
from .. import exception
from ._completions import complete_ident

###

name = 'stop'
cmdhelp = 'Stop program(s)'

###

def init_parser(parser):
	parser.add_argument('-i','--immediate-return', action='store_true', help='Dont wait for termination of programs and exit ASAP')
	parser.add_argument('-c','--core-dump', action='store_true', help='Stop program(s) to produce core dump (has to be also enabled in program configuration).')
	parser.add_argument('-E','--stop-and-exit', action='store_true', help='Stop all programs and exit Ramona server. Command-line default for:\n%(prog)s')
	parser.add_argument('-S','--stop-and-stay', action='store_true', help='Stop all programs but keep Ramona server running')
	parser.add_argument('program', nargs='*', help='Optionally specify program(s) in scope of the command. If none is given, all programs are considered in scope')

###

def complete(console, text, line, begidx, endidx):
	textst = text.strip()
	ret = []
	ret.extend(complete_ident(console, textst))
	return ret

###

def main(cnsapp, args):
	if args.stop_and_exit and len(args.program) > 0:
		raise exception.parameters_error('Cannot specify programs and -E option at once.')

	if args.stop_and_exit and args.stop_and_stay:
		raise exception.parameters_error('Cannot specify -T and -E option at once.')

	if len(args.program) == 0 and not args.stop_and_stay:
		args.stop_and_exit = True

	params={
		'immediate': args.immediate_return,
		'coredump': args.core_dump,
	}
	if args.stop_and_exit: params['mode'] = 'exit'
	elif args.stop_and_stay: params['mode'] = 'stay'
	if len(args.program) > 0: params['pfilter'] = args.program

	cnsapp.cnssvrcall(
		cnscom.callid_stop,
		json.dumps(params),
		auto_connect=True
	)

	if args.stop_and_exit:
		cnsapp.wait_for_svrexit()
