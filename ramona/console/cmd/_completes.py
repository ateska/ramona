import json
from ... import cnscom

def complete_ident(cnsapp, textst):
	ret = []
	statuses = cnsapp.cnsapp.svrcall(cnscom.callid_status, json.dumps({}), auto_connect=True)
	for st in json.loads(statuses):
		if st['ident'].startswith(textst) or textst == "":
			ret.append(st['ident'])
	return ret
