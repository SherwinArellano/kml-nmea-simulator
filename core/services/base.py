from core.track_manager import TrackManager
from core.transports import Transport
from abc import ABC, abstractmethod


class Service(ABC):
    tm: TrackManager
    transports: list[Transport]

    @abstractmethod
    async def start(self): ...

    @abstractmethod
    async def stop(self): ...
