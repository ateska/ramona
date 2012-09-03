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
	cnsapp.svrcall(
		cnscom.callid_stop,
		params=json.dumps(args.program),
		auto_connect=True
	)

