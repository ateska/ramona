import socket, ssl, pprint

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
ssl_sock = ssl.wrap_socket(s,
                 keyfile="../ca/console1.pem",
                 certfile="../ca/console1.crt",
# 				keyfile="../ca/selfsigned.pem",
# 				certfile="../ca/selfsigned.crt"
                ca_certs="../ca/demo-ca.crt",
                cert_reqs=ssl.CERT_REQUIRED
                )

ssl_sock.connect(('localhost', 10024))
# ssl_sock.connect("/tmp/aaaaaaa")

print repr(ssl_sock.getpeername())
print ssl_sock.cipher()
print pprint.pformat(ssl_sock.getpeercert())

ssl_sock.write("this is data from client...")
data = ssl_sock.read()
print data

ssl_sock.close()