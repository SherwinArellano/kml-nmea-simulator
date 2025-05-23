import asyncio
from typing import override
from core.messages import BuilderContext
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
                ctx = BuilderContext(
                    self.ti,
                    point,
                    nmea_types=self.cfg.nmea_types,
                    prev_point=prev_point,
                )
                self.builder.set_context(ctx)

                msgs = self.builder.build()
                for t in self.transports:
                    for m in msgs:
                        t.send(self.ti, m.encode())

                await asyncio.sleep(cfg.interval_ms / 1000)

                prev_point = point

            if not cfg.repeat:
                break
