from abc import ABC, abstractmethod
from core.models import TrackInfo


class Transport(ABC):
    @abstractmethod
    def send(self, ti: TrackInfo, payload: bytes) -> None: ...

    @abstractmethod
    def close(self) -> None: ...
