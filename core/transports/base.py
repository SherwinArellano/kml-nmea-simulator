from abc import ABC, abstractmethod
from core.models import TrackInfo
from core.utils import CallContext, CallParams
from dataclasses import dataclass


class TimestampParam(CallParams):
    def __init__(self, timestamp: float):
        self.timestamp = timestamp


class TransportContext(CallContext):
    def __init__(self, ti: TrackInfo, payload: bytes):
        super().__init__()
        self.ti = ti
        self.payload = payload


class Transport(ABC):
    @abstractmethod
    def send(self, ctx: TransportContext) -> None: ...

    @abstractmethod
    def close(self) -> None: ...
