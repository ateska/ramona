import json
from ... import cnscom
###

name = 'stop'
cmdhelp = 'Terminate subprocess(es)'

###

def init_parser(parser):
	parser.add_argument('program', nargs='*', help='Optionally specify program(s) in scope of the command')

###

def main(cnsapp, args):
	params={}
	if len(args.program) > 0: params['pfilter'] = args.program
	cnsapp.svrcall(
		cnscom.callid_stop,
		json.dumps(params),
		auto_connect=True
	)

