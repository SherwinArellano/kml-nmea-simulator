from .base import Service
from typing import override
import httpx
from core.messages import get_builder
from core.players import SimulatedPlayer
from core.models import Operation
from core.config import AppConfig
from dataclasses import asdict
from core.utils import run_tasks_and_stop_on_error, run_tasks_with_error_logging
import asyncio


class RESTService(Service):
    def __init__(self):
        app_cfg = AppConfig.get()
        rest_cfg = app_cfg.rest
        if not rest_cfg:
            raise RuntimeError("REST not set")

        self.base_url = rest_cfg.url
        self._client = httpx.AsyncClient()
        self._tasks: list[asyncio.Task] = []

    async def post_operation(self, operation: Operation):
        url = f"{self.base_url}/api/operations"
        response = await self._client.post(url, json=asdict(operation))
        response.raise_for_status()
        print(f"Posted operation with id: {operation.operation_id}")
        return response

    @override
    async def start(self):
        tasks: list[asyncio.Task] = []
        for track in self.tm.values():
            operation = Operation(
                operation_id=track.name,
                code_trailer="XX000XX",
                code_container="XXX0000",
                cod_prov="XX",
                cod_comune="X000",
                destination_port="X00",
                gps_position=track.coords[0],
                documents=None,
                start_date="",
                operation_date="",
                estimated_arrival_time="",
                operation_total_time=0,
            )

            tasks.append(asyncio.create_task(self.post_operation(operation)))

        results: list[httpx.Response] | None = await run_tasks_and_stop_on_error(tasks)
        if results:
            await self.start_polling()
        else:
            print("Tracks are not played, a backend error occurred.")

    @override
    async def stop(self):
        await self._client.aclose()

    async def start_polling(self):
        for ti in self.tm.values():
            print(f"▶ {ti.name}: {ti.cfg}")
            builder = get_builder(ti.cfg.mode)
            if self.transports:
                player = SimulatedPlayer(ti, builder, self.transports)
                self._tasks.append(asyncio.create_task(player.play()))

        await run_tasks_with_error_logging(self._tasks)
