import json
###

def main(svrapp, params):
	return json.dumps([{
		'ident': p.ident,
		'state': p.state,
		'stlbl': p.state_enum.labels[p.state],
		'pid'  : p.pid,
		'launch_cnt': p.launch_cnt,
		'start_time': p.start_time,
		'term_time': p.term_time,
		} for p in svrapp.roaster
	])
