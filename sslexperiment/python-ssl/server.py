import socket, ssl, pprint

bindsocket = socket.socket()
bindsocket.bind(('localhost', 10023))
bindsocket.listen(5)

while True:
    newsocket, fromaddr = bindsocket.accept()
    connstream = ssl.wrap_socket(newsocket,
                                 server_side=True,
                                 certfile="server.cert",
                                 keyfile="server.key",
                                 ssl_version=ssl.PROTOCOL_SSLv23,
                                 cert_reqs=ssl.CERT_REQUIRED,
                                 ca_certs="client.cert")
    try:
        print pprint.pformat(connstream.getpeercert())
    finally:
        connstream.shutdown(socket.SHUT_RDWR)
        connstream.close()