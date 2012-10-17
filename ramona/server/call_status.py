import json, time
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
		if p.subproc is not None: i['pid'] = p.subproc.pid
		if p.exit_status is not None: i['exit_status'] = p.exit_status
		if p.exit_time is not None: i['exit_time'] = p.exit_time
		if p.start_time is not None:
			i['start_time'] = p.start_time
			if p.exit_time is None:  i["uptime"] = time.time() - p.start_time
		if p.autorestart_cnt > 0: i['autorestart_cnt'] = p.autorestart_cnt
		ret.append(i)

	return json.dumps(ret)
