import json, logging, time
from ... import cnscom

###

name = 'who'
cmdhelp = 'Show is currently connected the server'

###

L = logging.getLogger('who')

###

def init_parser(parser):
	return

def main(cnsapp, args):
	print "Connected clients:"
	ret = cnsapp.cnssvrcall(
		cnscom.callid_who, 
		auto_connect=True
	)
	whoparsed = json.loads(ret)
	for whoitem in whoparsed:
		print "{}{} @ {}".format(
			'*' if whoitem['me'] else ' ',
			nice_addr(whoitem['descr'], whoitem['address']),
			time.strftime("%d-%m-%Y %H:%M:%S", time.localtime(whoitem['connected_at']))
		)

def nice_addr(descr, address):
	sock_family, sock_type, sock_proto, ssl_cert = descr

	if sock_proto == 'IPPROTO_TCP' and sock_family == 'AF_INET6':
		return " TCP [{}]:{}{}".format(address[0], address[1], nice_ssl(ssl_cert))
	elif sock_proto == 'IPPROTO_TCP' and sock_family == 'AF_INET':
		return " TCP {}:{}{}".format(address[0], address[1], nice_ssl(ssl_cert))
	elif sock_family == 'AF_UNIX':
		return "UNIX {}{}".format(address, nice_ssl(ssl_cert))
	else:
		return "{} {}".format(descr, address)

def nice_ssl(ssl_cert):
	if ssl_cert is None:
		return ""
	cert_subj = ssl_cert.get("subject", {})
	return " SSL (cn={})".format(cert_subj.get("commonName"))
