import json, logging
from ... import cnscom

###

name = 'who'
cmdhelp = 'Show connected consoles'

###

L = logging.getLogger('who')

###

def init_parser(parser):
	return

def main(cnsapp, args):
	print "getting users..."
	ret = cnsapp.cnssvrcall(
		cnscom.callid_who, 
		auto_connect=True
	)
	whoparsed = json.loads(ret)
	for who in whoparsed:
		# TODO: Better text representation
		print str(who['address']) + " --- " + who['connected_at']
	
	