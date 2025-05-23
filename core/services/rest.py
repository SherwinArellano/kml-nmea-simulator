import asyncio
from fastapi import FastAPI, HTTPException
from uvicorn import Config, Server
from concurrent.futures import ThreadPoolExecutor
from .base import Service
from core.messages import get_builder
from core.players import SimulatedPlayer
from typing import override


class RESTService(Service):
    def __init__(self):
        self.app = FastAPI()
        self._server: Server | None = None
        self._executor: ThreadPoolExecutor | None = None

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
        config = Config(self.app, host="0.0.0.0", port=8000, loop="asyncio")
        self._server = Server(config)

        await self._server.serve()

        #    If you instead want start() to return immediately and run in the
        #    background, you could do:
        #    asyncio.create_task(self._server.serve())
        #    return

    @override
    async def stop(self):
        if self._server:
            # Signal Uvicorn to stop its loop
            self._server.should_exit = True
