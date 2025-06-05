import socket
from .base import Transport
from typing import override
from core.config import AppConfig


class UDPTransport(Transport):
    def __init__(self, host: str, port: int):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.target = (host, port)

    @override
    def send(self, ctx):
        self.sock.sendto(ctx.payload, self.target)
        if AppConfig.get().verbose:
            print(f"[UDP] {ctx.payload.decode()}")

    @override
    def close(self):
        self.sock.close()
