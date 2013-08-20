import socket, ssl, pprint

bindsocket = socket.socket()
bindsocket.bind(('localhost', 10024))
bindsocket.listen(5)

while True:
    newsocket, fromaddr = bindsocket.accept()
    connstream = ssl.wrap_socket(newsocket,
                                 server_side=True,
                                 keyfile="../ca/server1.pem",
                                 certfile="../ca/server1.crt",
                                 ssl_version=ssl.PROTOCOL_SSLv23,
                                 cert_reqs=ssl.CERT_REQUIRED,
                                 ca_certs="../ca/demo-ca.crt")
    try:
        print pprint.pformat(connstream.getpeercert())
        print connstream.read()
        connstream.write("Data from server...")

    finally:
        connstream.shutdown(socket.SHUT_RDWR)
        connstream.close()