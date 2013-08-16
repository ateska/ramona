import sys, json, logging
from ... import cnscom
from .. import exception
from ._completions import complete_ident
###

name = 'tail'
cmdhelp = 'Display the last part of a log'

###

L = logging.getLogger('tail')

###

def init_parser(parser):
	parser.add_argument('-l','--log-stream', choices=['stdout','stderr'], default='stderr', help='Specify which standard stream to use (default is stderr)')
	parser.add_argument('-f', '--follow', action='store_true', help='Causes tail command to not stop when end of stream is reached, but rather to wait for additional data to be appended to the input')
	parser.add_argument('-n', '--lines', metavar='N', type=int, default=40, help='Output the last N lines, instead of the last 40')
	parser.add_argument('program', help='Specify the program in scope of the command')

###

def complete(console, text, line, begidx, endidx):
	textst = text.strip()
	ret = []
	ret.extend(complete_ident(console, textst))
	return ret

###


def main(cnsapp, args):

	params = {
		'program': args.program,
		'stream': args.log_stream,
		'lines': args.lines,
		'tailf': args.follow,
	}
	ret = cnsapp.cnssvrcall(
		cnscom.callid_tail,
		json.dumps(params),
		auto_connect=True
	)

	sys.stdout.write(ret)

	if not args.follow:
		return

	# Handle tail -f mode
	try:
		while 1:
			retype, params = cnscom.svrresp(cnsapp.ctlconsock, hang_detector=False)
			if retype == cnscom.resp_tailf_data:
				sys.stdout.write(params)
			else:
				raise RuntimeError("Unknown/invalid server response: {0}".format(retype))

	except KeyboardInterrupt:
		print

	except Exception, e:
		L.error("Tail failed: {0}".format(e))

	params = {
		'program': args.program,
		'stream': args.log_stream,
	}
	ret = cnsapp.cnssvrcall(
		cnscom.callid_tailf_stop,
		json.dumps(params)
	)
