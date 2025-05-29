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
        if cfg.filegen and cfg.filegen.enabled and cfg.filegen.mode == "single":
            print("Added transport: SingleFileTransport")
            if not cfg.filegen.outfile:
                raise KeyError("Missing required 'outfile' option in filegen mode")
            self.transports.append(SingleFileTransport(cfg.filegen.outfile))
        if cfg.filegen and cfg.filegen.enabled and cfg.filegen.mode == "multi":
            print("Added transport: MultiFilesTransport")
            if not cfg.filegen.outdir:
                raise KeyError("Missing required 'outdir' option in filegen mode")
            self.transports.append(MultiFilesTransport(cfg.filegen.outdir))
        if cfg.udp and cfg.udp.enabled:
            print("Added transport: UDPTransport")
            self.transports.append(UDPTransport(cfg.udp.host, cfg.udp.port))
        if cfg.mqtt and cfg.mqtt.enabled:
            print("Added transport: MQTTTransport")
            self.transports.append(
                MQTTTransport((cfg.mqtt.host, cfg.mqtt.port), cfg.mqtt.topic)
            )

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
