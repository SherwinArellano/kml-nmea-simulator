from .base import Service
from typing import override
import httpx
from core.messages import get_builder
from core.players import SimulatedPlayer
from core.models import Operation, OperationStatus, TrackInfo
from core.config import AppConfig
from dataclasses import asdict
from core.utils import (
    run_tasks_and_stop_on_error,
    run_tasks_with_error_logging,
    generate_code_trailer,
    generate_code_container,
)
from datetime import datetime, timedelta
import asyncio
import math


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
        return response

    async def put_operation(self, op_status: OperationStatus):
        url = f"{self.base_url}/api/operations/{op_status.operation_id}"
        response = await self._client.put(url, json=asdict(op_status))
        response.raise_for_status()
        return response

    @override
    async def start(self):
        track_operations: list[tuple[TrackInfo, Operation]] = []

        now = datetime.now()
        now_str = now.strftime("%Y-%m-%dT%H:%M:%S")
        for ti in self.tm.values():
            hours = (ti.total_dist / 1000.0) / ti.cfg.vel_kmh
            op_total = math.ceil(hours)
            eta = now + timedelta(hours=op_total)
            eta_str = eta.strftime("%Y-%m-%dT%H:%M:%S")

            operation = Operation(
                operation_id=ti.name,
                code_trailer=generate_code_trailer(),
                code_container=generate_code_container(),
                cod_prov="XX",
                cod_comune="X000",
                destination_port="X00",
                gps_position=ti.coords[0],
                documents=None,
                start_date=now_str,
                operation_date=now_str,
                estimated_arrival_time=eta_str,
                operation_total_time=op_total,
            )

            track_operations.append((ti, operation))

        results: list[httpx.Response] | None = await run_tasks_and_stop_on_error(
            [asyncio.create_task(self.post_operation(op)) for _, op in track_operations]
        )

        if results:
            for ti, operation in track_operations:
                task = asyncio.create_task(self.start_polling(ti, operation))
                self._tasks.append(task)
            await run_tasks_with_error_logging(self._tasks)
        else:
            msg = "[ERROR] Tracks are not played, a backend error occurred during POST."
            print(msg)

    @override
    async def stop(self):
        await self._client.aclose()

    async def start_polling(self, ti: TrackInfo, operation: Operation):
        op_status = OperationStatus(operation.operation_id, "01", None)
        await self.put_operation(op_status)

        try:
            print(f"▶ {ti.name}: {ti.cfg}")
            builder = get_builder(ti.cfg.mode)
            op_status.status_code = "02"
            if self.transports:
                player = SimulatedPlayer(ti, builder, self.transports)
                await player.play()
        except asyncio.CancelledError:  # keyboard interrupt (Ctrl + C)
            op_status.status_code = "02"
        except Exception as e:
            op_status.status_code = "03"
            op_status.description = str(e)
            await self.put_operation(op_status)
            print(f"An exception occured: {e}")
        finally:
            await self.put_operation(op_status)
