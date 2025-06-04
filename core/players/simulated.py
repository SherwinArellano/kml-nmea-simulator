import asyncio
from typing import override
from core.messages import MessageContext, TRKParams
from core.transports import TransportContext
from core.walker import walk_path
from .base import TrackPlayer
from core.config import AppConfig


class SimulatedPlayer(TrackPlayer):
    @override
    async def play(self):
        cfg = self.ti.cfg
        step = cfg.vel_kmh / 3.6 * (cfg.interval_ms / 1000)

        await asyncio.sleep(cfg.delay_ms / 1000)

        while True:
            self._emitter.emit("start", self.ti)
            await self._emitter.wait_for_complete()

            prev_point = None
            for point in walk_path(self.ti.coords, step, cfg.loop):
                ctx = MessageContext(self.ti, point)

                if cfg.mode != "nmea":  # trk, trk-container
                    ctx.set(TRKParams(prev_point))

                msgs = self.builder.build(ctx)
                for t in self.transports:
                    for m in msgs:
                        if AppConfig.get().verbose:
                            print(m)
                        t.send(TransportContext(self.ti, m.encode()))

                await asyncio.sleep(cfg.interval_ms / 1000)

                prev_point = point

            self._emitter.emit("finish", self.ti)
            await self._emitter.wait_for_complete()
            if not cfg.repeat:
                break
            else:
                self._emitter.emit("repeat", self.ti)
                await self._emitter.wait_for_complete()

    def repeat(self):
        """
        Decorator to register an async callback for the “repeat” event.

        Handler signature:
            async def handler(track_info: TrackInfo) -> None

        This event fires on each interval (i.e., every time a new coordinate is sent).
        """
        return self._emitter.on("repeat")
