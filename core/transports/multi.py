from .base import Transport
from typing import TextIO, override
import os
import re


class MultiFilesTransport(Transport):
    def __init__(self, outdir: str):
        self.outdir = outdir
        self.outfiles: dict[str, TextIO] = {}
        os.makedirs(outdir, exist_ok=True)

    @override
    def send(self, ti, payload):
        name = ti.name
        cfg = ti.cfg

        if name not in self.outfiles:
            kmlbase = os.path.splitext(os.path.basename(ti.path))[0]
            # make "snake-case" track name
            safe = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()
            ext = ".trk" if cfg.mode.startswith("trk") else ".nmea"
            path = os.path.join(self.outdir, f"{kmlbase}.{safe}{ext}")
            self.outfiles[name] = open(path, "w")

        self.outfiles[ti.name].write(payload.decode())

    @override
    def close(self):
        for of in self.outfiles.values():
            of.close()
