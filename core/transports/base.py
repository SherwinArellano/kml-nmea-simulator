from abc import ABC, abstractmethod
from core.models import TrackInfo
from dataclasses import dataclass


@dataclass
class TransportContext:
    ti: TrackInfo
    payload: bytes

    # Used by single transport:
    ts: float | None = None


class Transport(ABC):
    @abstractmethod
    def send(self, ctx: TransportContext) -> None: ...

    @abstractmethod
    def close(self) -> None: ...
