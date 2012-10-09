"""httpd-pyev -- A "hello world" web server implemented using pyev.

Copyright (c) 2009, Ben Weaver.  All rights reserved.
This software is issued "as is" under a BSD license
<http://orangesoda.net/license.html>.  All warranties disclaimed.

"""

import sys, io, socket, pyev, signal, logging

def handle(conn):
    data = conn.read(io.DEFAULT_BUFFER_SIZE)
    print('%d bytes:' % len(data), data)
    conn.write(b'HTTP/1.0 200 OK\r\nContent-Type: text/plain\r\nContent-Length:13\r\n\r\nHello, world!')

class server(object):

    def __init__(self, handle):
        self.handle = handle

    def __call__(self, addr='127.0.0.1', port=8080, backlog=None):
        sock = self.listen(addr, port, backlog)
        try:
            self.serve(sock)
        finally:
            sock.close()

    def listen(self, addr, port, backlog=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((addr, port))
        sock.listen(socket.SOMAXCONN if backlog is None else backlog)
        sock.setblocking(0)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        return sock

    def serve(self, sock, nevents=None):
        loop = pyev.default_loop()

        self.clients = {}
        main = pyev.Io(sock, pyev.EV_READ, loop, self.accept, data=sock)
        main.start()

        sigint = pyev.Signal(signal.SIGINT, loop, self.sigint, data=[main])
        sigint.start()

        loop.start()

    def sigint(self, watcher, events):
        try:
            for w in self.clients.keys():
                self.finish(w)
            for w in watcher.data:
                w.stop()
        finally:
            watcher.loop.unloop()

    def accept(self, watcher, events):
        sock, addr = watcher.data.accept()
        sock.setblocking(0)

        conn = connection(sock)
        wc = pyev.Io(sock, pyev.EV_READ, watcher.loop, self.read)
        self.clients[wc] = conn
        wc.start()

    def read(self, watcher, events):
        conn = self.clients[watcher]
        if conn._fill_buffer():
            self.handle(conn)
        else:
            self.finish(watcher)

    def finish(self, watcher):
        watcher.stop()
        self.clients.pop(watcher).close()

class connection(object):
    def start(self, loop, sock):
        self.msg = "HTTP/1.0 200 OK\r\nContent-Length: 5\r\n\r\nPong!\r\n"
        self.sock = sock
        self.write = self.write_msg
        self.writewatcher = pyev.Io(self.sock, pyev.EV_WRITE, loop, self.write)
        self.writewatcher.start()
 
    def write_msg(self, watcher, events):
        self.sock.send(self.msg)
        self.writewatcher.stop()
        self.sock.close()

if __name__ == '__main__':
    server(handle)()