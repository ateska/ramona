import socket
from OpenSSL import SSL

context = SSL.Context(SSL.SSLv23_METHOD)
context.use_privatekey_file('server.key')
context.use_certificate_file('server.cert')

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s = SSL.Connection(context, s)
s.bind(('localhost', 12345))
s.listen(5)

(connection, address) = s.accept()
while True:
	print repr(connection)
	print repr(connection.recv(65535))
