
name = 'server'
cmdhelp = 'Launch server in the foreground'

###

def init_parser(parser):
	return

###

def main(cnsapp, args):
	from ...utils import launch_server
	launch_server()
