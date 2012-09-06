import json
###

def main(svrapp, pfilter=None):
	l = svrapp.filter_roaster_iter(pfilter)
	ret = []
	for p in l:
		i = {
			'ident': p.ident,
			'state': p.state,
			'launch_cnt': p.launch_cnt,
		}
		if p.pid is not None: i['pid'] = p.pid
		if p.exit_status is not None: i['exit_status'] = p.exit_status
		if p.exit_time is not None: i['exit_time'] = p.exit_time
		if p.start_time is not None: i['start_time'] = p.start_time
		ret.append(i)

	return json.dumps(ret)
