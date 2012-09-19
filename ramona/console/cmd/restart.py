import json
from ... import cnscom
from ._completes import complete_ident

###

name = 'restart'
cmdhelp = 'Restart subprocess(es)'

###

def init_parser(parser):
	parser.add_argument('-n','--no-server-start', action='store_true', help='Avoid eventual automatic server start')
	parser.add_argument('-i','--immediate-return', action='store_true', help='Dont wait for start of subprocesses and return ASAP')
	parser.add_argument('-f','--force-start', action='store_true', help='Force restart of processes in FATAL state')
	parser.add_argument('program', nargs='*', help='Optionally specify program(s) in scope of the command')

###

def complete(cnsapp, text, line, begidx, endidx):
        textst = text.strip()
        ret = []
        ret.extend(complete_ident(cnsapp, textst))
        return ret

###

def main(cnsapp, args):
	params={
		'force':args.force_start,
		'immediate': args.immediate_return,
	}
	if len(args.program) > 0: params['pfilter'] = args.program

	cnsapp.svrcall(
		cnscom.callid_restart,
		json.dumps(params),
		auto_connect=args.no_server_start,
		auto_server_start=not args.no_server_start
	)
