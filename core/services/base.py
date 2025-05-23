from core.track_manager import TrackManager
from core.transports import Transport
from core.config import AppConfig
from abc import ABC, abstractmethod


class Service(ABC):
    def __init__(self, cfg: AppConfig, tm: TrackManager, transports: list[Transport]):
        self.cfg = cfg
        self.tm = tm
        self.transports = transports

    @abstractmethod
    async def start(self): ...
