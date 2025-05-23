from core.track_manager import TrackManager
from core.transports import Transport
from core.config import AppConfig
from abc import ABC, abstractmethod


class Service(ABC):
    cfg: AppConfig
    tm: TrackManager
    transports: list[Transport]

    @abstractmethod
    async def start(self): ...
