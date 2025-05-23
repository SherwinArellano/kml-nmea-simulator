from .base import Service
from typing import override
from fastapi import FastAPI, HTTPException
from core.players import SimulatedPlayer
from core.messages import get_builder
import asyncio
import uvicorn
from concurrent.futures import ThreadPoolExecutor


class RESTService(Service):
    def __init__(self):
        self.app = FastAPI()

        @self.app.get("/")
        def read_root():
            return {"Hello": "World"}

        @self.app.post("/simulate/{track_name}")
        async def simulate(track_name: str):
            if track_name not in self.tm.tracks:
                raise HTTPException(404, f"Track '{track_name}' not found")

            ti = self.tm.get(track_name)
            builder = get_builder(ti.cfg.mode)
            player = SimulatedPlayer(self.cfg, ti, builder, self.transports)
            asyncio.create_task(player.play())

            return {"status": "started", "track": track_name}

    @override
    async def start(self):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            ThreadPoolExecutor(),
            lambda: uvicorn.run(self.app, host="0.0.0.0", port=8000),
        )
