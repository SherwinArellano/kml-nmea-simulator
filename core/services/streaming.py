from .base import Service
from core.players import SimulatedPlayer, InstantPlayer
from core.messages import get_builder
from typing import override
from core.config import AppConfig
from core.utils import run_tasks_with_error_logging
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

            if self.transports:
                player = SimulatedPlayer(ti, builder, self.transports)
                self._tasks.append(asyncio.create_task(player.play()))

            if self.instant_transports:
                player = InstantPlayer(ti, builder, self.instant_transports)
                self._tasks.append(asyncio.create_task(player.play()))

        await run_tasks_with_error_logging(self._tasks)

    @override
    async def stop(self):
        for task in self._tasks:
            task.cancel()

        # ensure all cancellations are processed
        await run_tasks_with_error_logging(self._tasks)
        self._tasks.clear()
