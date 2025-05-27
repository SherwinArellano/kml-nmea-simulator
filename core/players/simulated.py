import asyncio
from typing import override
from core.messages import MessageContext, TRKParams
from core.transports import TransportContext
from core.walker import walk_path
from .base import TrackPlayer


class SimulatedPlayer(TrackPlayer):
    @override
    async def play(self):
        cfg = self.ti.cfg
        step = cfg.vel_kmh / 3.6 * (cfg.interval_ms / 1000)

        await asyncio.sleep(cfg.delay_ms / 1000)

        while True:
            prev_point = None
            for point in walk_path(self.ti.coords, step, cfg.loop):
                ctx = MessageContext(self.ti, point)

                if cfg.mode != "nmea":  # trk, trk-container
                    ctx.set(TRKParams(prev_point))

                msgs = self.builder.build(ctx)
                for t in self.transports:
                    for m in msgs:
                        t.send(TransportContext(self.ti, m.encode()))

                await asyncio.sleep(cfg.interval_ms / 1000)

                prev_point = point

            if not cfg.repeat:
                break
