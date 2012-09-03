import json
from ... import cnscom
###

name = 'start'
cmdhelp = 'Launch subprocess(es)'

###

def init_parser(parser):
	parser.add_argument('-n','--no-server-start', action='store_true', help='Avoid eventual automatic server start')
	parser.add_argument('program', nargs='*', help='Optionally specify program(s) in scope of the command')

###

def main(cnsapp, args):
	cnsapp.svrcall(
		cnscom.callid_start,
		params=json.dumps(args.program),
		auto_connect=args.no_server_start,
		auto_server_start=not args.no_server_start
	)

