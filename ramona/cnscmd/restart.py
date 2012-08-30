from .. import cnscom
###

name = 'restart'
cmdhelp = 'Restart subprocess(es)'

###

def init_parser(parser):
	return

###

def main(cnsapp, args):
	cnsapp.svrcall(cnscom.callid_restart, auto_connect=True)
