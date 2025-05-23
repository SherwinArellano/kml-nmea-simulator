import socket
from .base import Transport
from typing import override


class UDPTransport(Transport):
    def __init__(self, host: str, port: int):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.target = (host, port)

    @override
    def send(self, ctx):
        self.sock.sendto(ctx.payload, self.target)

    @override
    def close(self):
        self.sock.close()
