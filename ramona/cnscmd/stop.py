from .. import cnscom
###

name = 'stop'
cmdhelp = 'Terminate subprocess(es)'

###

def init_parser(parser):
	return

###

def main(cnsapp, args):
	cnsapp.svrcall(cnscom.callid_stop, auto_connect=True)

