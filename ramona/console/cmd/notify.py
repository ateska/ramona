import logging
from ... import cnscom

###

name = 'notify'
cmdhelp = 'Insert notification'

###

L = logging.getLogger('notify')

###

def init_parser(parser):
	return

def main(cnsapp, args):
	ret = cnsapp.cnssvrcall(
		cnscom.callid_notify,
		auto_connect=True
	)

	print ">>", ret
