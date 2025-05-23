from .base import Service
from core.players import SimulatedPlayer, InstantPlayer
from core.messages import get_builder
from typing import override
import asyncio


class StreamingService(Service):
    @override
    async def start(self):
        tasks = []
        for ti in self.tm.values():
            print(f"▶ {ti.name}: {ti.cfg}")
            builder = get_builder(ti.cfg.mode)

            if self.cfg.filegen_mode:
                player = InstantPlayer(self.cfg, ti, builder, self.transports)
            else:
                player = SimulatedPlayer(self.cfg, ti, builder, self.transports)

            tasks.append(asyncio.create_task(player.play()))
        await asyncio.gather(*tasks)
