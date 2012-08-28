import json, time
from .. import cnscom
###

name = 'status'
cmdhelp = 'Show status of subprocess(es)'

###

def init_parser(parser):
	return

###

def main(cnsapp, args):
	ret = cnsapp.svrcall(cnscom.callid_status, auto_connect=True)
	status = json.loads(ret)
	
	# TODO: Probably more info to be printed
	for sp in status:

		details = []

		pid = sp.get('pid')
		if pid is not None: details.append("pid:{0}".format(pid))

		details.append("launches:{0}".format(sp['launch_cnt']))

		t = sp.get('start_time')
		if t is not None: details.append("start_time:{0}".format(time.strftime("%d-%m-%Y %H:%M:%S",time.localtime(t))))

		t = sp.get('term_time')
		if t is not None: details.append("term_time:{0}".format(time.strftime("%d-%m-%Y %H:%M:%S",time.localtime(t))))

		print "{0:<16} {1:<10} {2}".format(
			sp.get('ident', '???'), 
			sp.get('stlbl', '???'),
			','.join(details),
			)

