from .base import Transport, TimestampParam
from typing import override
import os


class SingleFileTransport(Transport):
    def __init__(self, outfile: str):
        od = os.path.dirname(outfile) or "."
        os.makedirs(od, exist_ok=True)
        self.outfile = open(outfile, "w", buffering=1)
        self.buffer: list[tuple[float, bytes]] = []

    @override
    def send(self, ctx):
        ts = ctx.get(TimestampParam).timestamp
        self.buffer.append((ts, ctx.payload))

    def flush(self):
        self.buffer.sort(key=lambda x: x[0])
        for _, payload in self.buffer:
            self.outfile.write(payload.decode())

    @override
    def close(self):
        self.outfile.close()
