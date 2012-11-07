import json
from ... import cnscom

def complete_ident(console, textst):
	ret = []
	statuses = console.cnsapp.cnssvrcall(cnscom.callid_status, json.dumps({}), auto_connect=True)
	for st in json.loads(statuses):
		if st['ident'].startswith(textst) or textst == "":
			ret.append(st['ident'])
	return ret
