from core.config import AppConfig
from core.track_manager import TrackManager
from core.transports import (
    Transport,
    SingleFileTransport,
    MultiFilesTransport,
    UDPTransport,
    MQTTTransport,
)
from .base import Service
import asyncio


class ServiceManager:
    def __init__(self, tm: TrackManager):
        self.tm = tm
        self.services: list[Service] = []
        self.transports: list[Transport] = []

        # build transports
        cfg = AppConfig.get()
        if cfg.filegen_mode == "single":
            print("Added transport: SingleFileTransport")
            self.transports.append(SingleFileTransport(cfg.outfile))
        if cfg.filegen_mode == "multi":
            print("Added transport: MultiFilesTransport")
            self.transports.append(MultiFilesTransport(cfg.outdir))
        if cfg.udp_target:
            print("Added transport: UDPTransport")
            self.transports.append(UDPTransport(*cfg.udp_target))
        if cfg.mqtt_broker:
            print("Added transport: MQTTTransport")
            self.transports.append(MQTTTransport(cfg.mqtt_broker, cfg.mqtt_topic))

    def register(self, service: Service):
        service.tm = self.tm
        service.transports = self.transports
        self.services.append(service)

    async def start_all(self):
        tasks = []
        for service in self.services:
            print(f"Started service: {service.__class__.__name__}")
            tasks.append(asyncio.create_task(service.start()))
        await asyncio.gather(*tasks)

    async def stop_all(self):
        for svc in self.services:
            await svc.stop()
