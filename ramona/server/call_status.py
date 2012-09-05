import json
###

def main(svrapp, pfilter=None):
	l = svrapp.filter_roaster_iter(pfilter)
	return json.dumps([{
		'ident': p.ident,
		'state': p.state,
		'stlbl': p.state_enum.labels[p.state],
		'pid'  : p.pid,
		'launch_cnt': p.launch_cnt,
		'start_time': p.start_time,
		'exit_time': p.exit_time,
		} for p in l
	])
