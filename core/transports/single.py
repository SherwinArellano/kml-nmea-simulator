from .base import Transport
from typing import override
import os


class SingleFileTransport(Transport):
    def __init__(self, outfile: str):
        od = os.path.dirname(outfile) or "."
        os.makedirs(od, exist_ok=True)
        self.outfile = open(outfile, "w", buffering=1)

    @override
    def send(self, ti, payload):
        self.outfile.write(payload.decode())

    @override
    def close(self):
        self.outfile.close()
