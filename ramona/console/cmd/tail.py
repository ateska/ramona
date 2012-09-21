import json
from ... import cnscom
from .. import exception
from ._completes import complete_ident
###

name = 'tail'
cmdhelp = 'Tail log of specified program'

###

def init_parser(parser):
	parser.add_argument('-l','--log-stream', choices=['stdout','stderr'], default='stderr', help='Specify which log stream to use in tail (default is stderr)')
	parser.add_argument('program', help='Specify program(s) in scope of the command')

###

def complete(cnsapp, text, line, begidx, endidx):
	textst = text.strip()
	ret = []
	ret.extend(complete_ident(cnsapp, textst))
	return ret

###


def main(cnsapp, args):

	params = {
		'program': args.program,
		'stream': args.log_stream,
	}
	ret = cnsapp.svrcall(
		cnscom.callid_tail,
		json.dumps(params),
		auto_connect=True
	)

	print ret
