from typing import override
from core.config import AppConfig
from core.messages import MessageContext, TRKParams
from core.transports import TransportContext, SingleFileTransport, TimestampParam
from core.walker import walk_path
from .base import TrackPlayer
import time


class InstantPlayer(TrackPlayer):
    def generate_messages(self):
        """Yields (timestamp, raw_payload_bytes) in track-order."""
        ti = self.ti
        cfg = self.ti.cfg

        start = time.time() + cfg.delay_ms / 1000
        step_s = cfg.interval_ms / 1000
        step_m = cfg.vel_kmh / 3.6 * step_s

        prev_point = None
        for idx, point in enumerate(walk_path(ti.coords, step_m, cfg.loop)):
            epoch_s = start + idx * step_s
            ctx = MessageContext(self.ti, point, epoch_s)

            if ti.cfg.mode != "nmea":  # trk, trk-container
                ctx.set(TRKParams(prev_point))

            msgs = self.builder.build(ctx)

            for m in msgs:
                yield epoch_s, m.encode()

            prev_point = point

    @override
    async def play(self):
        app_cfg = AppConfig.get()

        self._emitter.emit("start", self.ti)
        await self._emitter.wait_for_complete()

        for ts, payload in self.generate_messages():
            for t in self.transports:
                ctx = TransportContext(self.ti, payload)

                if app_cfg.filegen and app_cfg.filegen.mode == "single":
                    ctx.set(TimestampParam(ts))

                t.send(ctx)

        self._emitter.emit("end", self.ti)
        await self._emitter.wait_for_complete()

        # hacky solution for now to flush data from single file transport
        for t in self.transports:
            if isinstance(t, SingleFileTransport):
                t.flush()
