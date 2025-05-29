from .base import Service
from core.players import SimulatedPlayer, InstantPlayer
from core.messages import get_builder
from typing import override
from core.config import AppConfig
import asyncio


class StreamingService(Service):
    def __init__(self):
        self._tasks: list[asyncio.Task] = []

    @override
    async def start(self):
        for ti in self.tm.values():
            print(f"▶ {ti.name}: {ti.cfg}")
            builder = get_builder(ti.cfg.mode)

            cfg = AppConfig.get()
            if cfg.filegen and not cfg.filegen.streaming:
                player = InstantPlayer(ti, builder, self.transports)
            else:
                player = SimulatedPlayer(ti, builder, self.transports)

            task = asyncio.create_task(player.play())
            self._tasks.append(task)

        await asyncio.gather(*self._tasks, return_exceptions=True)

    @override
    async def stop(self):
        for task in self._tasks:
            task.cancel()

        # ensure all cancellations are processed
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
