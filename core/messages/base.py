from abc import ABC, abstractmethod
from core.models import TrackInfo
from core.utils import CallContext
from dataclasses import dataclass


class MessageContext(CallContext):
    def __init__(
        self, ti: TrackInfo, point: tuple[float, float], epoch_s: float | None = None
    ):
        super().__init__()
        self.ti = ti
        self.point = point
        self.epoch_s = epoch_s


class MessageBuilder(ABC):
    @abstractmethod
    def build(self, ctx: MessageContext) -> list[str]: ...
