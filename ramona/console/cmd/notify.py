import json, logging
from ... import cnscom

###

name = 'notify'
cmdhelp = 'Insert notification'

###

L = logging.getLogger('notify')

###

def init_parser(parser):
	parser.add_argument('-t','--target', action='store', choices=['now','daily'], default='now', help='Specify target of notification. Default is "now".')
	parser.add_argument('-s','--subject', action='store', help="Specify subject of notification.")
	parser.add_argument('text', help='Body of notification.')

def main(cnsapp, args):
	params = {
		'target': args.target,
		'subject': args.subject,
		'text': args.text
	}
	ret = cnsapp.cnssvrcall(
		cnscom.callid_notify,
		json.dumps(params),
		auto_connect=True
	)
