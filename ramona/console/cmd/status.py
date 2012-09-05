import json, time, logging
from ... import cnscom
from .. import exception
###

name = 'status'
cmdhelp = 'Show status of subprocess(es)'

###

L = logging.getLogger('status')

###

def init_parser(parser):
	parser.add_argument('program', nargs='*', help='Optionally specify program(s) in scope of the command')

###

def main(cnsapp, args):
	params={}
	if len(args.program) > 0: params['pfilter'] = args.program
	ret = cnsapp.svrcall(
		cnscom.callid_status, 
		json.dumps(params),
		auto_connect=True
	)

	status = json.loads(ret)
	
	# TODO: Probably more info to be printed
	for sp in status:

		details = []

		pid = sp.get('pid')
		if pid is not None: details.append("pid:{0}".format(pid))

		details.append("launches:{0}".format(sp['launch_cnt']))

		t = sp.get('start_time')
		if t is not None: details.append("start_time:{0}".format(time.strftime("%d-%m-%Y %H:%M:%S",time.localtime(t))))

		t = sp.get('exit_time')
		if t is not None: details.append("exit_time:{0}".format(time.strftime("%d-%m-%Y %H:%M:%S",time.localtime(t))))

		print "{0:<16} {1:<10} {2}".format(
			sp.get('ident', '???'), 
			sp.get('stlbl', '???'),
			','.join(details),
			)

