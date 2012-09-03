from ... import cnscom
###

name = 'start'
cmdhelp = 'Launch subprocess(es)'

###

def init_parser(parser):
	return

###

def main(cnsapp, args):
	cnsapp.svrcall(cnscom.callid_start, auto_server_start=True)

