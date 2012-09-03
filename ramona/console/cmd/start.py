from ... import cnscom
###

name = 'start'
cmdhelp = 'Launch subprocess(es)'

###

def init_parser(parser):
	parser.add_argument('-n','--no-server-start', action='store_true', help='Avoid eventual automatic server start')

###

def main(cnsapp, args):
	cnsapp.svrcall(cnscom.callid_start, auto_connect=args.no_server_start, auto_server_start=not args.no_server_start)

